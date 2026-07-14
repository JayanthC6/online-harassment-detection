"""
Loads the trained baseline model and classifies new messages.

Swap this module's internals for the DistilBERT model later without
changing the Flask route that calls it — keep the same predict_message()
function signature.
"""
import os
import sys
import joblib

sys.path.append(os.path.dirname(__file__))
from preprocess import preprocess

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

CLASS_TO_CATEGORY = {0: "hate_speech", 1: "offensive_language", 2: "none"}
CLASS_TO_LABEL = {0: "harassing", 1: "harassing", 2: "non_harassing"}

_clf = None
_vectorizer = None


def _load():
    global _clf, _vectorizer
    if _clf is None:
        clf_path = os.path.join(MODEL_DIR, "baseline_clf.joblib")
        vec_path = os.path.join(MODEL_DIR, "baseline_vectorizer.joblib")
        if not (os.path.exists(clf_path) and os.path.exists(vec_path)):
            raise FileNotFoundError(
                "Model not found. Run `python ml/train_baseline.py` first."
            )
        _clf = joblib.load(clf_path)
        _vectorizer = joblib.load(vec_path)
    return _clf, _vectorizer


def predict_message(text: str) -> dict:
    """Classify a single message. Returns label, category, and confidence."""
    clf, vectorizer = _load()

    cleaned = preprocess(text)
    if not cleaned:
        return {
            "label": "non_harassing",
            "category": "none",
            "confidence": 1.0,
            "note": "Message had no usable content after cleaning.",
        }

    X = vectorizer.transform([cleaned])
    pred_class = int(clf.predict(X)[0])
    proba = clf.predict_proba(X)[0]
    confidence = float(proba[list(clf.classes_).index(pred_class)])

    return {
        "label": CLASS_TO_LABEL[pred_class],
        "category": CLASS_TO_CATEGORY[pred_class],
        "confidence": round(confidence, 4),
    }


if __name__ == "__main__":
    examples = [
        "You're worthless, just disappear already.",
        "Great job on the presentation today!",
        "I know where you live, watch your back.",
    ]
    for ex in examples:
        print(ex, "->", predict_message(ex))
