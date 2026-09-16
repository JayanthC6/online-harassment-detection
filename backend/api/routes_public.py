from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from werkzeug.utils import secure_filename
import os

from services.prediction_service import PredictionService
from services.admin_service import AdminService
from core.exceptions import AppException
from ml.ocr import extract_and_classify
from services.parsers import parse_whatsapp_txt, parse_instagram_json
import db
from ml.chatbot import generate_chat_response, extract_text_from_file, analyze_file_content
from ml.adapters.threat_intel import mask_pii, extract_pii

def sanitize_result_for_public(result: dict) -> dict:
    """Masks PII in a result dictionary before returning to frontend or passing to chatbot."""
    if not isinstance(result, dict):
        return result
    res = result.copy()
    if "text_preview" in res and res["text_preview"]:
        res["text_preview"] = mask_pii(res["text_preview"])
    if "text_full" in res and res["text_full"]:
        res["text_full"] = mask_pii(res["text_full"])
    if "evidence" in res and res["evidence"]:
        res["evidence"] = mask_pii(res["evidence"])
    if "content" in res and res["content"]:
        res["content"] = mask_pii(res["content"])
    if "extracted_text" in res and res["extracted_text"]:
        res["extracted_text"] = mask_pii(res["extracted_text"])
    if "transcript" in res and res["transcript"]:
        res["transcript"] = mask_pii(res["transcript"])
    if "messages" in res and isinstance(res["messages"], list):
        res["messages"] = [m.copy() for m in res["messages"] if isinstance(m, dict)]
        for m in res["messages"]:
            if "text" in m and m["text"]:
                m["text"] = mask_pii(m["text"])
    return res

# Import the shared limiter instance (defined in extensions.py to avoid circular imports)
from extensions import limiter

MAX_CHAT_FILE_MB = 50
ALLOWED_CHAT_FILE_EXTS = {
    "pdf", "txt", "md", "log", "csv", "json", "docx",
    "py", "html", "xml", "png", "jpg", "jpeg", "webp"
}

# Summarize is imported safely
try:
    from ml.summarize import summarize_complaint
except Exception:
    pass

# Transformer explainability — only available when HF_TOKEN + captum are present
try:
    from ml import explain_transformer as _explain_tx
    _explain_tx_available = True
except Exception:
    _explain_tx_available = False

public_bp = Blueprint("public", __name__)


def _get_limiter():
    """Lazy accessor for the Flask-Limiter instance attached to the app."""
    return getattr(current_app, 'limiter', None)

ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "m4a", "mp4", "mov", "webm", "ogg"}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_AUDIO_SIZE_MB = 50
MAX_IMAGE_SIZE_MB = 10

def allowed_file(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in allowed_set

@public_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "database": "mongodb" if AdminService.get_stats() else "in-memory (not persistent)",
        "model": PredictionService.get_active_model_name(),
    })

from api.dependencies import token_optional

@public_bp.route("/predict/instant", methods=["POST"])
@token_optional
@limiter.limit("30 per minute")
def predict_instant(token_data):
    # Per-route payload guard: 32 KB max
    cl = request.content_length
    if cl is not None and cl > 32 * 1024:
        return jsonify({"error": "Payload too large. Maximum 32 KB for /predict/instant."}), 413

    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    persist = data.get("persist", False)

    if not text or not isinstance(text, str):
        return jsonify({"error": "Request body must include a non-empty 'text' string."}), 400
    if len(text) > 2000:
        return jsonify({"error": "Text exceeds 2000 character limit."}), 400

    result = PredictionService.classify_text(text)
    result["text_preview"] = text[:120]
    result["text_full"] = text
    result["timestamp"] = datetime.utcnow().isoformat()
    
    actor_id = token_data.get("user") if token_data else "Anonymous"
    result["actor_id"] = actor_id
    result = PredictionService.attach_risk_and_similarity(result, text)

    try:
        from services.guidance_service import GuidanceService
        primary_label = result.get("primary_label", "none")
        primary_confidence = result.get("confidence", 0.0)
        secondary_labels = result.get("secondary_labels", {})
        risk_score = result.get("risk_score", 0)
        
        guidance_data = GuidanceService.get_guidance(
            primary_label, primary_confidence, secondary_labels, risk_score
        )
        
        result["guidance"] = guidance_data
        result["guidance_snippet"] = guidance_data.get("evidence_checklist", ["No specific guidance required."])[0]
    except Exception as e:
        result["guidance"] = None
        result["guidance_snippet"] = f"Error fetching guidance: {e}"

    # If the user is logged in and persist is true, log it to db for history tracking
    if persist and token_data:
        is_public_user = token_data.get("role", "").lower() == "user"
        history_entry = {
            "actor_id": actor_id,
            "user_id": token_data.get("user"),
            "source": "self_serve" if is_public_user else "platform",
            "type": "text",
            "content": text,
            "ai_analysis": result,
            **result
        }
        
        if is_public_user:
            history_entry["text_preview"] = mask_pii(history_entry.get("text_preview", ""))
            history_entry["text_full"] = mask_pii(history_entry.get("text_full", ""))
            history_entry["evidence"] = mask_pii(history_entry.get("evidence", ""))
            history_entry["content"] = mask_pii(history_entry.get("content", ""))
            
        AdminService.log_message(history_entry)

    result.pop("embedding", None)
    result.pop("_id", None)
    
    # Mask API response for normal or anonymous users
    is_admin = token_data and token_data.get("role", "").lower() in ["admin", "moderator"]
    if not is_admin:
        result = sanitize_result_for_public(result)
        
    return jsonify(result)

@public_bp.route("/predict", methods=["POST"])
@token_optional
@limiter.limit("30 per minute")
def predict(token_data):
    # Per-route payload guard: 32 KB max for plain-text JSON requests.
    # Text is capped at 2000 chars (~8 KB); 32 KB rejects garbage before parsing.
    cl = request.content_length
    if cl is not None and cl > 32 * 1024:
        return jsonify({"error": "Payload too large. Maximum 32 KB for /predict."}), 413
    import os
    ext_api_key = os.environ.get("EXTENSION_API_KEY")
    if ext_api_key:
        origin = request.headers.get("Origin", "")
        # Bypass for local frontend development
        if not (origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:")):
            if request.headers.get("X-Extension-Api-Key") != ext_api_key:
                return jsonify({"error": "Unauthorized: Invalid or missing X-Extension-Api-Key"}), 401

    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    persist = data.get("persist", False)

    if not text or not isinstance(text, str):
        return jsonify({"error": "Request body must include a non-empty 'text' string."}), 400
    if len(text) > 2000:
        return jsonify({"error": "Text exceeds 2000 character limit."}), 400

    result = PredictionService.classify_text(text)
    result["pii_categories"] = extract_pii(text)
    result["text_preview"] = text[:120]
    result["text_full"] = text  # full text needed by /predict/explain for LIG
    result["timestamp"] = datetime.utcnow().isoformat()
    result["actor_id"] = data.get("actor_id", "Anonymous")
    result = PredictionService.attach_risk_and_similarity(result, text)

    if persist and token_data:
        is_public_user = token_data.get("role", "").lower() == "user"
        if is_public_user:
            masked_result = result.copy()
            masked_result["text_preview"] = mask_pii(result.get("text_preview", ""))
            masked_result["text_full"] = mask_pii(result.get("text_full", ""))
            masked_result["evidence"] = mask_pii(result.get("evidence", ""))
            masked_result["source"] = "self_serve"
            masked_result["user_id"] = token_data.get("user")
            AdminService.log_message(masked_result)
        else:
            result_copy = result.copy()
            result_copy["source"] = "platform"
            result_copy["user_id"] = token_data.get("user")
            AdminService.log_message(result_copy)

    result.pop("embedding", None)
    result.pop("_id", None)  # MongoDB ObjectId is not JSON serializable
    
    # Mask API response for normal or anonymous users
    is_admin = token_data and token_data.get("role", "").lower() in ["admin", "moderator"]
    if not is_admin:
        result = sanitize_result_for_public(result)
        
    return jsonify(result)

DEMO_EXAMPLES = {
    "harassment_example": "Everyone would be better off if you just disappeared. We know you don't belong here, and soon everyone else will too.",
    "phishing_example": "URGENT: Your account has been suspended for security reasons. Click here to verify your identity immediately: http://paypa1.com/account-verify-now",
    "threat_example": "I know where you live. If you don't send me $5000 in Bitcoin by tomorrow, I will ruin your life and hurt your family.",
    "clean_example": "Hey, are we still meeting for lunch tomorrow at 12? Let me know!"
}

@public_bp.route("/demo/analyze", methods=["POST"])
@limiter.limit("5 per minute")
def demo_analyze():
    data = request.get_json(silent=True) or {}
    example_id = data.get("example_id")
    
    if example_id not in DEMO_EXAMPLES:
        return jsonify({"error": "Invalid or missing example_id. Only preset examples are permitted."}), 400
        
    text = DEMO_EXAMPLES[example_id]
    
    # Process the text using the ML pipeline
    result = PredictionService.classify_text(text)
    result["text_preview"] = text[:120]
    result["timestamp"] = datetime.utcnow().isoformat()
    result["actor_id"] = "DemoVisitor"
    result = PredictionService.attach_risk_and_similarity(result, text)
    
    # Generate guidance without persisting to DB
    try:
        from services.guidance_service import GuidanceService
        primary_label = result.get("primary_label", "none")
        primary_confidence = result.get("confidence", 0.0)
        secondary_labels = result.get("secondary_labels", {})
        risk_score = result.get("risk_score", 0)
        
        guidance_data = GuidanceService.get_guidance(
            primary_label, primary_confidence, secondary_labels, risk_score
        )
        
        result["severity"] = result.get("severity_tier", "Unknown")
        
        checklist = guidance_data.get("evidence_checklist", [])
        if checklist and len(checklist) > 0:
            result["guidance_snippet"] = checklist[0]
        else:
            result["guidance_snippet"] = "No specific guidance required."
    except Exception as e:
        result["severity"] = "Unknown"
        result["guidance_snippet"] = f"Error fetching guidance: {e}"
        
    result.pop("embedding", None)
    return jsonify(result)

@public_bp.route("/predict/batch", methods=["POST"])
@token_optional
@limiter.limit("30 per minute")
def predict_batch(token_data):
    data = request.get_json(silent=True) or {}
    texts = data.get("texts", [])
    persist = data.get("persist", False)

    if not isinstance(texts, list) or len(texts) == 0:
        return jsonify({"error": "Provide a non-empty 'texts' array."}), 400
    if len(texts) > 50:
        return jsonify({"error": "Batch limit is 50 messages."}), 400

    results = []
    for text in texts:
        if not isinstance(text, str) or not text.strip():
            results.append({"error": "Empty or invalid text", "text_preview": str(text)[:120]})
            continue
        if len(text) > 2000:
            results.append({"error": "Text exceeds 2000 character limit", "text_preview": text[:120]})
            continue

        r = PredictionService.classify_text(text)
        r["pii_categories"] = extract_pii(text)
        r["text_preview"] = text[:120]
        r["timestamp"] = datetime.utcnow().isoformat()
        r = PredictionService.attach_risk_and_similarity(r, text)
        
        if persist and token_data:
            is_public_user = token_data.get("role", "").lower() == "user"
            if is_public_user:
                masked_r = r.copy()
                masked_r["text_preview"] = mask_pii(r.get("text_preview", ""))
                masked_r["evidence"] = mask_pii(r.get("evidence", ""))
                masked_r["source"] = "self_serve"
                masked_r["user_id"] = token_data.get("user")
                AdminService.log_message(masked_r)
            else:
                r_copy = r.copy()
                r_copy["source"] = "platform"
                r_copy["user_id"] = token_data.get("user")
                AdminService.log_message(r_copy)
            
        r.pop("embedding", None)
        r.pop("_id", None)  # MongoDB ObjectId is not JSON serializable
        
        # Mask API response for normal or anonymous users
        is_admin = token_data and token_data.get("role", "").lower() in ["admin", "moderator"]
        if not is_admin:
            r = sanitize_result_for_public(r)
            
        results.append(r)

    return jsonify({"results": results, "count": len(results)})

@public_bp.route("/predict/audio", methods=["POST"])
@token_optional
@limiter.limit("30 per minute")
def predict_audio(token_data):
    # Per-route payload guard: 50 MB for audio uploads
    cl = request.content_length
    if cl is not None and cl > 50 * 1024 * 1024:
        return jsonify({"error": "Payload too large. Maximum 50 MB for audio uploads."}), 413
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Send it as multipart/form-data under key 'file'."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type '.{ext}'. Allowed: {sorted(ALLOWED_AUDIO_EXTENSIONS)}"}), 400

    import tempfile
    from ml.transcribe import transcribe
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        file.save(tmp.name)
        file_size_mb = os.path.getsize(tmp.name) / (1024 * 1024)
        if file_size_mb > MAX_AUDIO_SIZE_MB:
            os.remove(tmp.name)
            return jsonify({"error": f"File too large ({file_size_mb:.1f}MB). Max {MAX_AUDIO_SIZE_MB}MB."}), 413

        try:
            transcript_data = transcribe(tmp.name)
            transcript_text = transcript_data["text"]
        except Exception as e:
            os.remove(tmp.name)
            return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

    os.remove(tmp.name)

    if not transcript_text:
        return jsonify({"error": "Could not detect any speech in the file."}), 400

    result = PredictionService.classify_text(transcript_text)
    result["pii_categories"] = extract_pii(transcript_text)
    result["text_preview"] = transcript_text[:120]
    result["timestamp"] = datetime.utcnow().isoformat()
    result["transcript"] = transcript_text
    result["actor_id"] = request.form.get("actor_id", "Anonymous")
    result = PredictionService.attach_risk_and_similarity(result, transcript_text)

    persist = request.form.get("persist", "false").lower() == "true"
    if persist and token_data:
        is_public_user = token_data.get("role", "").lower() == "user"
        if is_public_user:
            masked_result = result.copy()
            masked_result["transcript"] = mask_pii(result.get("transcript", ""))
            masked_result["text_preview"] = mask_pii(result.get("text_preview", ""))
            masked_result["evidence"] = mask_pii(result.get("evidence", ""))
            masked_result["source"] = "self_serve"
            masked_result["user_id"] = token_data.get("user")
            AdminService.log_message(masked_result)
        else:
            result_copy = result.copy()
            result_copy["source"] = "platform"
            result_copy["user_id"] = token_data.get("user")
            AdminService.log_message(result_copy)

    result.pop("embedding", None)
    
    # Mask API response for normal or anonymous users
    is_admin = token_data and token_data.get("role", "").lower() in ["admin", "moderator"]
    if not is_admin:
        result = sanitize_result_for_public(result)
        
    return jsonify(result)

@public_bp.route("/predict/screenshot", methods=["POST"])
@token_optional
@limiter.limit("30 per minute")
def predict_screenshot(token_data):
    # Per-route payload guard: 10 MB for image uploads
    cl = request.content_length
    if cl is not None and cl > 10 * 1024 * 1024:
        return jsonify({"error": "Payload too large. Maximum 10 MB for screenshot uploads."}), 413
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type. Allowed: {ALLOWED_IMAGE_EXTENSIONS}"}), 400

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        file.save(tmp.name)
        file_size_mb = os.path.getsize(tmp.name) / (1024 * 1024)
        if file_size_mb > MAX_IMAGE_SIZE_MB:
            os.remove(tmp.name)
            return jsonify({"error": f"File too large. Max {MAX_IMAGE_SIZE_MB}MB."}), 413

        try:
            result = extract_and_classify(tmp.name, PredictionService.classify_text)
        except Exception as e:
            os.remove(tmp.name)
            return jsonify({"error": f"OCR/Analysis failed: {str(e)}"}), 500

    os.remove(tmp.name)
    extracted_text = result.get("extracted_text", "")
    if not extracted_text:
        return jsonify({"error": "No text detected in screenshot."}), 400

    result["pii_categories"] = extract_pii(extracted_text)
    result["timestamp"] = datetime.utcnow().isoformat()
    result["actor_id"] = request.form.get("actor_id", "Anonymous")
    result["platform"] = request.form.get("platform", "generic")
    result = PredictionService.attach_risk_and_similarity(result, extracted_text)

    persist = request.form.get("persist", "false").lower() == "true"
    if persist and token_data:
        is_public_user = token_data.get("role", "").lower() == "user"
        if is_public_user:
            masked_result = result.copy()
            masked_result["text_preview"] = mask_pii(result.get("text_preview", "") or extracted_text[:120])
            masked_result["evidence"] = mask_pii(result.get("evidence", ""))
            masked_result["extracted_text"] = mask_pii(result.get("extracted_text", ""))
            masked_result["source"] = "self_serve"
            masked_result["user_id"] = token_data.get("user")
            AdminService.log_message(masked_result)
        else:
            result_copy = result.copy()
            result_copy["source"] = "platform"
            result_copy["user_id"] = token_data.get("user")
            AdminService.log_message(result_copy)

    result.pop("embedding", None)
    
    # Mask API response for normal or anonymous users
    is_admin = token_data and token_data.get("role", "").lower() in ["admin", "moderator"]
    if not is_admin:
        result = sanitize_result_for_public(result)
        
    return jsonify(result)

@public_bp.route("/predict/file", methods=["POST"])
@token_optional
@limiter.limit("30 per minute")
def predict_file(token_data):
    # Per-route payload guard: 50 MB for document uploads
    cl = request.content_length
    if cl is not None and cl > 50 * 1024 * 1024:
        return jsonify({"error": "Payload too large. Maximum 50 MB for file uploads."}), 413
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_CHAT_FILE_EXTS:
        return jsonify({"error": f"Unsupported file type. Allowed: {ALLOWED_CHAT_FILE_EXTS}"}), 400

    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
    tmp.close() # Close immediately to release Windows file lock
    
    try:
        file.save(tmp.name)
        file_size_mb = os.path.getsize(tmp.name) / (1024 * 1024)
        if file_size_mb > 50:
            os.remove(tmp.name)
            return jsonify({"error": f"File too large. Max 50MB."}), 413

        try:
            extracted_text = extract_text_from_file(tmp.name, file.filename)
        except Exception as e:
            os.remove(tmp.name)
            return jsonify({"error": f"Extraction failed: {str(e)}"}), 500
    finally:
        if os.path.exists(tmp.name):
            try:
                os.remove(tmp.name)
            except Exception:
                pass
    if not extracted_text or not extracted_text.strip():
        return jsonify({"error": "No text detected in file."}), 400
        
    extracted_text = extracted_text.strip()
    # If text is excessively long, truncate to first 10,000 chars for engine processing
    if len(extracted_text) > 10000:
        extracted_text = extracted_text[:10000]

    result = PredictionService.classify_text(extracted_text)
    result["pii_categories"] = extract_pii(extracted_text)
    result["timestamp"] = datetime.utcnow().isoformat()
    result["actor_id"] = request.form.get("actor_id", "Anonymous")
    
    # Generate bot summary for the file text
    try:
        from ml.chatbot import analyze_file_content
        sanitized_for_bot = mask_pii(extracted_text)
        bot_summary = analyze_file_content(sanitized_for_bot, file.filename)
        result["bot_summary_text"] = bot_summary
    except Exception as e:
        result["bot_summary_text"] = "Error: Could not generate bot summary."

    result["text_preview"] = extracted_text[:120]
    result["text_full"] = extracted_text
    result = PredictionService.attach_risk_and_similarity(result, extracted_text)

    persist = request.form.get("persist", "false").lower() == "true"
    if persist and token_data:
        is_public_user = token_data.get("role", "").lower() == "user"
        if is_public_user:
            masked_result = result.copy()
            masked_result["text_preview"] = mask_pii(result.get("text_preview", ""))
            masked_result["text_full"] = mask_pii(result.get("text_full", ""))
            masked_result["evidence"] = mask_pii(result.get("evidence", ""))
            masked_result["source"] = "self_serve"
            masked_result["user_id"] = token_data.get("user")
            AdminService.log_message(masked_result)
        else:
            result_copy = result.copy()
            result_copy["source"] = "platform"
            result_copy["user_id"] = token_data.get("user")
            AdminService.log_message(result_copy)

    result.pop("embedding", None)
    
    # Mask API response for normal or anonymous users
    is_admin = token_data and token_data.get("role", "").lower() in ["admin", "moderator"]
    if not is_admin:
        result = sanitize_result_for_public(result)
        
    return jsonify(result)

@public_bp.route("/summarize", methods=["POST"])
def summarize():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    category = data.get("category", "none")
    confidence = data.get("confidence", 0)

    if not text or not isinstance(text, str):
        return jsonify({"error": "Request body must include a non-empty 'text' string."}), 400

    try:
        result = summarize_complaint(text, category, confidence)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@public_bp.route("/predict/conversation", methods=["POST"])
@token_optional
@limiter.limit("30 per minute")
def predict_conversation(token_data):
    # Per-route payload guard: 512 KB for conversation JSON
    cl = request.content_length
    if cl is not None and cl > 512 * 1024:
        return jsonify({"error": "Payload too large. Maximum 512 KB for /predict/conversation."}), 413
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])
    persist = data.get("persist", False)

    if not isinstance(messages, list) or len(messages) == 0:
        return jsonify({"error": "Provide a non-empty 'messages' array."}), 400
    if len(messages) > 100:
        return jsonify({"error": "Conversation limit is 100 messages."}), 400

    valid_messages = []
    for msg in messages:
        if isinstance(msg, dict) and "text" in msg and isinstance(msg["text"], str) and msg["text"].strip():
            msg["pii_categories"] = extract_pii(msg["text"])
            valid_messages.append(msg)
            
    if not valid_messages:
        return jsonify({"error": "No valid messages provided."}), 400

    try:
        result = PredictionService.analyze_conversation(valid_messages)
        
        if persist and token_data:
            is_public_user = token_data.get("role", "").lower() == "user"
            if is_public_user:
                masked_result = result.copy()
                masked_result["evidence"] = mask_pii(result.get("evidence", ""))
                masked_messages = []
                for m in valid_messages:
                    masked_m = m.copy()
                    masked_m["text"] = mask_pii(m.get("text", ""))
                    masked_messages.append(masked_m)
                masked_result["messages"] = masked_messages
                masked_result["source"] = "self_serve"
                masked_result["user_id"] = token_data.get("user")
                AdminService.log_conversation(masked_result)
            else:
                result_copy = result.copy()
                result_copy["source"] = "platform"
                result_copy["user_id"] = token_data.get("user")
                AdminService.log_conversation(result_copy)
            
        # Mask API response for normal or anonymous users
        is_admin = token_data and token_data.get("role", "").lower() in ["admin", "moderator"]
        if not is_admin:
            result = sanitize_result_for_public(result)
            
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@public_bp.route("/predict/conversation/import", methods=["POST"])
@token_optional
@limiter.limit("30 per minute")
def import_conversation(token_data):
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in {"txt", "json"}:
        return jsonify({"error": f"Unsupported file type. Allowed: txt, json"}), 400
        
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        file.save(tmp.name)
        file_path = tmp.name
        
    try:
        if ext == "txt":
            messages = parse_whatsapp_txt(file_path)
            platform = "whatsapp"
        elif ext == "json":
            messages = parse_instagram_json(file_path)
            platform = "instagram"
            
        if not messages:
            return jsonify({"error": "Failed to extract any messages from the file."}), 400
            
        # Attach platform to first message so it carries over
        messages[0]["platform"] = platform
        
        for msg in messages:
            msg["pii_categories"] = extract_pii(msg.get("text", ""))
        
        result = PredictionService.analyze_conversation(messages)
        
        persist = request.form.get("persist", "false").lower() == "true"
        if persist and token_data:
            is_public_user = token_data.get("role", "").lower() == "user"
            if is_public_user:
                masked_result = result.copy()
                masked_result["evidence"] = mask_pii(result.get("evidence", ""))
                masked_messages = []
                for m in messages:
                    masked_m = m.copy()
                    masked_m["text"] = mask_pii(m.get("text", ""))
                    masked_messages.append(masked_m)
                masked_result["messages"] = masked_messages
                masked_result["source"] = "self_serve"
                masked_result["user_id"] = token_data.get("user")
                AdminService.log_conversation(masked_result)
            else:
                result_copy = result.copy()
                result_copy["source"] = "platform"
                result_copy["user_id"] = token_data.get("user")
                AdminService.log_conversation(result_copy)
            
        # Mask API response for normal or anonymous users
        is_admin = token_data and token_data.get("role", "").lower() in ["admin", "moderator"]
        if not is_admin:
            result = sanitize_result_for_public(result)
            
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@public_bp.route("/chat", methods=["POST"])
@limiter.limit("30 per minute")
def chat():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    message = data.get("message")
    persona = data.get("persona", "user")
    prediction_context = data.get("prediction_context")

    if not session_id or not message:
        return jsonify({"error": "session_id and message are required."}), 400

    # Retrieve history
    history = db.get_chat_session(session_id)
    
    # Append user message
    user_msg = {"role": "user", "content": message}
    history.append(user_msg)
    
    # Sanitize context payload before sending to LLM
    if prediction_context:
        prediction_context = sanitize_result_for_public(prediction_context)

    # Generate response
    ai_response_text = generate_chat_response(history, persona, prediction_context)
    
    # Append ai response
    ai_msg = {"role": "assistant", "content": ai_response_text}
    history.append(ai_msg)
    
    # Save history
    db.save_chat_session(session_id, history)
    
    return jsonify({"response": ai_response_text, "session_id": session_id})

@public_bp.route("/chat/<session_id>", methods=["GET"])
def get_chat(session_id):
    history = db.get_chat_session(session_id)
    return jsonify({"messages": history})


@public_bp.route("/chat/file", methods=["POST"])
def chat_file_upload():
    """Accept a file, extract its text, and return an AI analysis."""
    session_id = request.form.get("session_id")
    persona = request.form.get("persona", "user")
    
    if not session_id:
        return jsonify({"error": "session_id is required."}), 400

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Send it under key 'file'."}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_CHAT_FILE_EXTS:
        return jsonify({
            "error": f"Unsupported file type '.{ext}'. Allowed: {sorted(ALLOWED_CHAT_FILE_EXTS)}"
        }), 400

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        file.save(tmp.name)
        file_size_mb = os.path.getsize(tmp.name) / (1024 * 1024)

        if file_size_mb > MAX_CHAT_FILE_MB:
            os.remove(tmp.name)
            return jsonify({"error": f"File too large ({file_size_mb:.1f} MB). Max {MAX_CHAT_FILE_MB} MB."}), 413

        try:
            extracted_text = extract_text_from_file(tmp.name, file.filename)
        except RuntimeError as e:
            os.remove(tmp.name)
            return jsonify({"error": str(e)}), 400
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)

    if not extracted_text or not extracted_text.strip():
        return jsonify({"error": "No readable text found in the file."}), 400

    # Sanitize text before sending to LLM
    sanitized_text = mask_pii(extracted_text)

    # Run AI analysis
    analysis = analyze_file_content(sanitized_text, file.filename, persona)

    # Persist as a chat turn so the conversation remembers the file
    history = db.get_chat_session(session_id)
    history.append({"role": "user", "content": f"[Uploaded file: **{file.filename}**]"})
    history.append({"role": "assistant", "content": analysis})
    db.save_chat_session(session_id, history)

    return jsonify({
        "response": analysis,
        "filename": file.filename,
        "size_mb": round(file_size_mb, 2),
        "session_id": session_id,
    })


@public_bp.route("/predict/explain", methods=["POST"])
def predict_explain():
    """
    Lazy token-level explainability endpoint.
    Called only when the Incident Intelligence panel is opened — NOT during /predict.

    Body (JSON):
        text  (str, required)  — the message to explain
        label (str, required)  — which label to attribute against (primary or secondary)

    Returns 200 with one of two shapes:
        Neural label:   { label, is_neural: true,  method, tokens: [{token, score, sign}] }
        Symbolic label: { label, is_neural: false, reason, rule_evidence: [...] }
    """
    body = request.get_json(force=True, silent=True) or {}
    text = body.get("text", "").strip()
    label = body.get("label", "").strip()

    if not text:
        return jsonify({"error": "'text' is required."}), 400
    if not label:
        return jsonify({"error": "'label' is required."}), 400

    # ── Symbolic-only label or module unavailable: return rule evidence ──
    is_neural = _explain_tx_available and _explain_tx.is_neural_label(label)

    if not is_neural:
        try:
            adapter = PredictionService.get_adapter()
            rule_hits = adapter.explain_heuristics(text, {label: 1.0}) if hasattr(adapter, "explain_heuristics") else []
        except Exception:
            rule_hits = []

        if not _explain_tx_available:
            reason = "Explainability module unavailable (HF_TOKEN or captum missing)."
        else:
            reason = (
                f"'{label}' is detected by the rule engine, not the neural model. "
                "Gradient attribution would produce meaningless output for this category."
            )

        return jsonify({
            "label": label,
            "is_neural": False,
            "reason": reason,
            "rule_evidence": rule_hits,
        })

    # ── Neural label: compute LIG attributions ──
    try:
        result = _explain_tx.compute_ig_attributions(text, label)
        result["is_neural"] = True
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        import traceback
        print(f"[/predict/explain] Unexpected error: {e}")
        traceback.print_exc()
        return jsonify({"error": "Internal error during attribution computation."}), 500
