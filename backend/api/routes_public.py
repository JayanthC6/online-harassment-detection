from flask import Blueprint, request, jsonify
from datetime import datetime
from werkzeug.utils import secure_filename
import os

from services.prediction_service import PredictionService
from services.admin_service import AdminService
from core.exceptions import AppException
from ml.ocr import extract_and_classify
from services.parsers import parse_whatsapp_txt, parse_instagram_json
import db
from ml.chatbot import generate_chat_response

# Summarize is imported safely
try:
    from ml.summarize import summarize_complaint
except Exception:
    pass

public_bp = Blueprint("public", __name__)

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

@public_bp.route("/predict", methods=["POST"])
def predict():
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

    if not text or not isinstance(text, str):
        return jsonify({"error": "Request body must include a non-empty 'text' string."}), 400
    if len(text) > 2000:
        return jsonify({"error": "Text exceeds 2000 character limit."}), 400

    result = PredictionService.classify_text(text)
    result["text_preview"] = text[:120]
    result["timestamp"] = datetime.utcnow().isoformat()
    result["actor_id"] = data.get("actor_id", "Anonymous")
    result = PredictionService.attach_risk_and_similarity(result, text)

    AdminService.log_message(result)

    result.pop("embedding", None)
    return jsonify(result)

@public_bp.route("/predict/batch", methods=["POST"])
def predict_batch():
    data = request.get_json(silent=True) or {}
    texts = data.get("texts", [])

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
        r["text_preview"] = text[:120]
        r["timestamp"] = datetime.utcnow().isoformat()
        r = PredictionService.attach_risk_and_similarity(r, text)
        
        AdminService.log_message(r)
            
        r.pop("embedding", None)
        results.append(r)

    return jsonify({"results": results, "count": len(results)})

@public_bp.route("/predict/audio", methods=["POST"])
def predict_audio():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Send it as multipart/form-data under key 'file'."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type '.{ext}'. Allowed: {sorted(ALLOWED_AUDIO_EXTENSIONS)}"}), 400

    import tempfile
    from ml.transcribe import transcribe_audio
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        file.save(tmp.name)
        file_size_mb = os.path.getsize(tmp.name) / (1024 * 1024)
        if file_size_mb > MAX_AUDIO_SIZE_MB:
            os.remove(tmp.name)
            return jsonify({"error": f"File too large ({file_size_mb:.1f}MB). Max {MAX_AUDIO_SIZE_MB}MB."}), 413

        try:
            transcript_text = transcribe_audio(tmp.name)
        except Exception as e:
            os.remove(tmp.name)
            return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

    os.remove(tmp.name)

    if not transcript_text:
        return jsonify({"error": "Could not detect any speech in the file."}), 400

    result = PredictionService.classify_text(transcript_text)
    result["text_preview"] = transcript_text[:120]
    result["timestamp"] = datetime.utcnow().isoformat()
    result["transcript"] = transcript_text
    result["actor_id"] = request.form.get("actor_id", "Anonymous")
    result = PredictionService.attach_risk_and_similarity(result, transcript_text)

    AdminService.log_message({**result, "text_preview": transcript_text[:120]})

    result.pop("embedding", None)
    return jsonify(result)

@public_bp.route("/predict/screenshot", methods=["POST"])
def predict_screenshot():
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

    result["timestamp"] = datetime.utcnow().isoformat()
    result["actor_id"] = request.form.get("actor_id", "Anonymous")
    result["platform"] = request.form.get("platform", "generic")
    result = PredictionService.attach_risk_and_similarity(result, extracted_text)

    AdminService.log_message({**result, "text_preview": extracted_text[:120]})

    result.pop("embedding", None)
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
def predict_conversation():
    data = request.get_json(silent=True) or {}
    messages = data.get("messages", [])

    if not isinstance(messages, list) or len(messages) == 0:
        return jsonify({"error": "Provide a non-empty 'messages' array."}), 400
    if len(messages) > 100:
        return jsonify({"error": "Conversation limit is 100 messages."}), 400

    valid_messages = []
    for msg in messages:
        if isinstance(msg, dict) and "text" in msg and isinstance(msg["text"], str) and msg["text"].strip():
            valid_messages.append(msg)
            
    if not valid_messages:
        return jsonify({"error": "No valid messages provided."}), 400

    try:
        result = PredictionService.analyze_conversation(valid_messages)
        AdminService.log_conversation(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@public_bp.route("/predict/conversation/import", methods=["POST"])
def import_conversation():
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
        
        result = PredictionService.analyze_conversation(messages)
        AdminService.log_conversation(result)
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@public_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    message = data.get("message")

    if not session_id or not message:
        return jsonify({"error": "session_id and message are required."}), 400

    # Retrieve history
    history = db.get_chat_session(session_id)
    
    # Append user message
    user_msg = {"role": "user", "content": message}
    history.append(user_msg)
    
    # Generate response
    ai_response_text = generate_chat_response(history)
    
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

