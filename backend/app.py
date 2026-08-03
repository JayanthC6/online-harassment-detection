"""
Flask backend for the Online Harassment Detection System.

Endpoints:
    GET  /health              -> liveness check, also reports DB connection status
    POST /predict             -> classify a single text message
    POST /predict/batch       -> classify multiple text messages at once
    POST /predict/audio       -> transcribe an audio/video file, then classify it
    POST /predict/screenshot  -> OCR a screenshot, then classify the extracted text
    POST /summarize           -> Groq-powered incident summary for a flagged report
    GET  /admin/stats         -> summary stats for the dashboard
    GET  /admin/recent        -> recently flagged messages (sorted by risk score)
    GET  /admin/daily_counts  -> daily flagged counts + anomaly flags

Storage: uses MongoDB if MONGODB_URI is set in a .env file (see db.py),
otherwise falls back to in-memory storage automatically so the app still
works without a database configured.

Model selection: uses DistilBERT automatically if you've trained one and
dropped it in backend/models/distilbert/. Falls back to the TF-IDF baseline
otherwise, so the app always works even before you've done the transformer
training step.
"""
import os
import sys

# Import torch first on Windows to avoid DLL conflicts with other libraries
try:
    import torch
except Exception:
    pass

import tempfile
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()  # reads MONGODB_URI from a .env file if present

sys.path.append(os.path.join(os.path.dirname(__file__), "ml"))
from predict import predict_message as predict_baseline
import predict_transformer
import db
from ocr import extract_and_classify

# Explainability — only available for the baseline model
try:
    import explain as explain_module
    _explain_available = True
except Exception:
    _explain_available = False

# Similarity detection — lazy load to avoid slow startup
_similarity_available = False
try:
    from similarity import find_similar_reports, embed_text
    _similarity_available = True
except Exception:
    pass

app = Flask(__name__)
CORS(app)  # allow the React dev server to call this API

ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "m4a", "mp4", "mov", "webm", "ogg"}
MAX_AUDIO_SIZE_MB = 50

# Map category string -> class index for explain.py
CATEGORY_TO_CLASS = {"hate_speech": 0, "offensive_language": 1, "none": 2}


def _active_model_name() -> str:
    """Return the name of the currently active model."""
    return "distilbert" if predict_transformer.is_available() else "baseline"


def classify_text(text: str) -> dict:
    """Routes to DistilBERT if trained, else the baseline model."""
    if predict_transformer.is_available():
        return predict_transformer.predict_message(text)
    result = predict_baseline(text)
    result["model"] = "baseline"

    # Explainability: attach word-level contributions for baseline model
    if _explain_available and result.get("category"):
        class_idx = CATEGORY_TO_CLASS.get(result["category"])
        if class_idx is not None:
            result["explanation"] = explain_module.explain_prediction(
                text, class_idx, top_n=5
            )
    return result


def _attach_risk_and_similarity(result: dict, text_for_embedding: str) -> dict:
    """
    Attach risk_score and duplicate detection to a prediction result.
    Used by all prediction endpoints.
    """
    # Risk scoring
    result["risk_score"] = db.compute_risk_score(
        result.get("category", "none"),
        result.get("confidence", 0),
    )

    # Similarity detection (only for harassing content)
    if result["label"] == "harassing" and _similarity_available:
        try:
            existing = db.get_all_flagged()
            matches, embedding = find_similar_reports(text_for_embedding, existing)
            result["embedding"] = embedding  # store with the logged entry
            if matches:
                result["similar_reports"] = matches[:3]  # top 3 most similar
                # Assign a cluster ID based on the first match
                result["cluster_id"] = f"cluster-{hash(matches[0]['text_preview']) % 10000:04d}"
        except Exception:
            pass  # gracefully degrade if similarity fails

    return result


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "database": "mongodb" if db.is_persistent() else "in-memory (not persistent)",
        "model": _active_model_name(),
    })


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")

    if not text or not isinstance(text, str):
        return jsonify({"error": "Request body must include a non-empty 'text' string."}), 400

    if len(text) > 2000:
        return jsonify({"error": "Text exceeds 2000 character limit."}), 400

    result = classify_text(text)
    result["text_preview"] = text[:120]
    result["timestamp"] = datetime.utcnow().isoformat()

    result = _attach_risk_and_similarity(result, text)

    if result["label"] == "harassing":
        db.log_flagged_message(result)

    # Don't send the embedding vector to the client
    result.pop("embedding", None)

    return jsonify(result)


@app.route("/predict/batch", methods=["POST"])
def predict_batch():
    """Classify multiple messages in one request.

    Body: {"texts": ["msg1", "msg2", ...]}   (max 50)
    Returns: {"results": [{...}, {...}, ...]}
    """
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

        r = classify_text(text)
        r["text_preview"] = text[:120]
        r["timestamp"] = datetime.utcnow().isoformat()
        r = _attach_risk_and_similarity(r, text)
        if r["label"] == "harassing":
            db.log_flagged_message(r)
        r.pop("embedding", None)
        results.append(r)

    return jsonify({"results": results, "count": len(results)})


@app.route("/predict/audio", methods=["POST"])
def predict_audio():
    """
    Accepts an uploaded audio/video file, transcribes it with Whisper, then
    classifies the transcript. This is "video harassment detection" in the
    honest sense: it reads what was said, not what's visually happening in
    frame -- see backend/ml/transcribe.py for why that scope line was drawn.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Send it as multipart/form-data under key 'file'."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type '.{ext}'. Allowed: {sorted(ALLOWED_AUDIO_EXTENSIONS)}"}), 400

    filename = secure_filename(file.filename)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, filename)
        file.save(tmp_path)

        size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        if size_mb > MAX_AUDIO_SIZE_MB:
            return jsonify({"error": f"File too large ({size_mb:.1f}MB). Limit is {MAX_AUDIO_SIZE_MB}MB."}), 400

        try:
            from transcribe import transcribe_and_classify
            classifier = "distilbert" if predict_transformer.is_available() else "baseline"
            result = transcribe_and_classify(tmp_path, classifier=classifier)
        except Exception as e:
            return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

    result["timestamp"] = datetime.utcnow().isoformat()
    result["source_filename"] = filename

    transcript_text = result.get("transcript", "")
    result = _attach_risk_and_similarity(result, transcript_text)

    if result["label"] == "harassing":
        db.log_flagged_message({**result, "text_preview": transcript_text[:120]})

    result.pop("embedding", None)
    return jsonify(result)


ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
MAX_IMAGE_SIZE_MB = 10

@app.route("/predict/screenshot", methods=["POST"])
def predict_screenshot():
    """
    Accepts an uploaded image file, extracts text via OCR, then
    classifies the extracted text.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Send it as multipart/form-data under key 'file'."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": f"Unsupported file type '.{ext}'. Allowed: {sorted(ALLOWED_IMAGE_EXTENSIONS)}"}), 400

    filename = secure_filename(file.filename)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, filename)
        file.save(tmp_path)

        size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        if size_mb > MAX_IMAGE_SIZE_MB:
            return jsonify({"error": f"File too large ({size_mb:.1f}MB). Limit is {MAX_IMAGE_SIZE_MB}MB."}), 400

        try:
            classifier = "distilbert" if predict_transformer.is_available() else "baseline"
            result = extract_and_classify(tmp_path, classifier=classifier)
        except Exception as e:
            return jsonify({"error": f"OCR extraction failed: {str(e)}"}), 500

    result["timestamp"] = datetime.utcnow().isoformat()
    result["source_filename"] = filename

    extracted_text = result.get("extracted_text", "")
    result = _attach_risk_and_similarity(result, extracted_text)

    if result["label"] == "harassing":
        db.log_flagged_message({**result, "text_preview": extracted_text[:120]})

    result.pop("embedding", None)
    return jsonify(result)


@app.route("/summarize", methods=["POST"])
def summarize():
    """
    Generate a structured incident summary using Groq API.
    Only for summarizing the user's own text — NOT for legal advice.
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    category = data.get("category", "none")
    confidence = data.get("confidence", 0)

    if not text or not isinstance(text, str):
        return jsonify({"error": "Request body must include a non-empty 'text' string."}), 400

    try:
        from summarize import summarize_complaint
        result = summarize_complaint(text, category, confidence)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/admin/stats", methods=["GET"])
def admin_stats():
    stats = db.get_stats()
    stats["model"] = _active_model_name()
    return jsonify(stats)


@app.route("/admin/recent", methods=["GET"])
def admin_recent():
    limit = int(request.args.get("limit", 20))
    recent = db.get_recent(limit)
    # Strip embeddings from response (large vectors, not needed by frontend)
    for r in recent:
        r.pop("embedding", None)
    return jsonify(recent)


@app.route("/admin/daily_counts", methods=["GET"])
def admin_daily_counts():
    """Return daily flagged message counts + anomaly detection results."""
    days = int(request.args.get("days", 30))
    daily = db.get_daily_counts(days)
    anomalies = db.detect_anomalies(daily)
    return jsonify({"daily_counts": daily, "anomalies": anomalies})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)