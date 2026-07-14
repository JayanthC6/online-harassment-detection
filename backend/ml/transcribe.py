"""
Transcribes audio/video to text using OpenAI's Whisper, then hands the
transcript to the existing text classifier (predict.py or predict_transformer.py).

This is the "video-based harassment detection" feature -- it works by
extracting what was SAID, not by analyzing the video frames themselves.
That's a deliberate scope decision: analyzing visual behavior in video
would need a different kind of model entirely and there's no ethical
public dataset to train it on. Transcription + text classification is
the honest, buildable version of "video harassment detection."

First run downloads the model weights (~150MB for 'base', one-time,
needs internet). Subsequent runs use the cached copy.

Usage:
    python transcribe.py path/to/file.mp4
"""
import os
import sys

import whisper

sys.path.append(os.path.dirname(__file__))

_whisper_model = None

# Model size tradeoff: 'base' is a reasonable default (fast, decent accuracy).
# 'small' or 'medium' are more accurate but slower -- fine on a GPU, painful on CPU.
WHISPER_MODEL_SIZE = "base"


def _load_whisper():
    global _whisper_model
    if _whisper_model is None:
        print(f"Loading Whisper '{WHISPER_MODEL_SIZE}' model (first call only)...")
        _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)
    return _whisper_model


def transcribe(file_path: str) -> dict:
    """
    Transcribes an audio or video file. Whisper uses ffmpeg internally,
    so it accepts most common formats (mp3, wav, mp4, mov, m4a...) directly
    -- no manual audio extraction step needed.

    Returns: {"text": str, "language": str, "duration_sec": float}
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    model = _load_whisper()
    result = model.transcribe(file_path)

    return {
        "text": result["text"].strip(),
        "language": result.get("language", "unknown"),
        "segments": len(result.get("segments", [])),
    }


def transcribe_and_classify(file_path: str, classifier="baseline") -> dict:
    """
    Full pipeline: audio/video file -> transcript -> harassment classification.

    classifier: "baseline" (default, always available) or "distilbert"
                (only works once you've trained and placed that model).
    """
    transcript = transcribe(file_path)

    if not transcript["text"]:
        return {
            "label": "non_harassing",
            "category": "none",
            "confidence": 1.0,
            "transcript": "",
            "note": "No speech detected in file.",
        }

    if classifier == "distilbert":
        from predict_transformer import predict_message
    else:
        from predict import predict_message

    result = predict_message(transcript["text"])
    result["transcript"] = transcript["text"]
    result["language"] = transcript["language"]
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py path/to/file.mp4")
        sys.exit(1)

    result = transcribe_and_classify(sys.argv[1])
    print(f"Transcript: {result['transcript']}")
    print(f"Label: {result['label']}  Category: {result['category']}  Confidence: {result['confidence']}")
