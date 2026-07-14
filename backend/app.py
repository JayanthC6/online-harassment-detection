"""
Flask backend for the Online Harassment Detection System.

Endpoints:
    GET  /health              -> liveness check, also reports DB connection status
    POST /predict              -> classify a single text message
    POST /predict/audio         -> transcribe an audio/video file, then classify it
    GET  /admin/stats           -> summary stats for the dashboard
    GET  /admin/recent          -> recently flagged messages

Storage: uses MongoDB if MONGODB_URI is set in a .env file (see db.py and
.env.example), otherwise falls back to in-memory storage automatically so
the app still works without a database configured.

Model selection: uses DistilBERT automatically if you've trained one and
dropped it in backend/models/distilbert/ (see notebooks/02_train_distilbert.ipynb).
Falls back to the TF-IDF baseline otherwise, so the app always works even
before you've done the transformer training step.
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

app = Flask(__name__)
CORS(app)  # allow the React dev server to call this API

ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "m4a", "mp4", "mov", "webm", "ogg"}
MAX_AUDIO_SIZE_MB = 50


def classify_text(text: str) -> dict:
    """Routes to DistilBERT if trained, else the baseline model."""
    if predict_transformer.is_available():
        return predict_transformer.predict_message(text)
    result = predict_baseline(text)
    result["model"] = "baseline"
    return result


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "database": "mongodb" if db.is_persistent() else "in-memory (not persistent)",
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
    return jsonify(db.get_stats())


@app.route("/admin/recent", methods=["GET"])
def admin_recent():
    limit = int(request.args.get("limit", 20))
    return jsonify(db.get_recent(limit))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)