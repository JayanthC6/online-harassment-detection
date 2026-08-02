"""
Flask backend for the Online Harassment Detection System.

Endpoints:
    GET  /health              -> liveness check, also reports DB connection status
    POST /predict             -> classify a single text message
    POST /predict/batch       -> classify multiple text messages at once
    POST /predict/audio       -> transcribe an audio/video file, then classify it
    GET  /admin/stats         -> summary stats for the dashboard
    GET  /admin/recent        -> recently flagged messages

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

# Explainability — only available for the baseline model
try:
    import explain as explain_module
    _explain_available = True
except Exception:
    _explain_available = False

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

    if result["label"] == "harassing":
        db.log_flagged_message(result)

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
        if r["label"] == "harassing":
            db.log_flagged_message(r)
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

    if result["label"] == "harassing":
        db.log_flagged_message({**result, "text_preview": result.get("transcript", "")[:120]})

    return jsonify(result)


@app.route("/admin/stats", methods=["GET"])
def admin_stats():
    stats = db.get_stats()
    stats["model"] = _active_model_name()
    return jsonify(stats)


@app.route("/admin/recent", methods=["GET"])
def admin_recent():
    limit = int(request.args.get("limit", 20))
    return jsonify(db.get_recent(limit))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)