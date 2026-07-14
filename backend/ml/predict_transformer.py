"""
Loads the fine-tuned DistilBERT model (from train_transformer.py or the
Colab notebook) and classifies new messages.

Same function signature as predict.py's predict_message() on purpose, so
app.py can swap between them without changing route logic.

Imports for torch/transformers are deliberately lazy (inside functions, not
at module top level) so that importing this module doesn't crash the whole
Flask app on machines that haven't installed those libraries yet. You only
need them once you actually train and use DistilBERT.
"""
import os

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "distilbert")

CLASS_TO_CATEGORY = {0: "hate_speech", 1: "offensive_language", 2: "none"}
CLASS_TO_LABEL = {0: "harassing", 1: "harassing", 2: "non_harassing"}

_model = None
_tokenizer = None
_device = None


def is_available() -> bool:
    """Check whether a fine-tuned model has been trained and dropped in place."""
    if not os.path.exists(os.path.join(MODEL_DIR, "config.json")):
        return False
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        return False
    return True


def _load():
    global _model, _tokenizer, _device
    if _model is None:
        import torch
        from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification

        if not is_available():
            raise FileNotFoundError(
                f"No DistilBERT model found at {MODEL_DIR}, or torch/transformers "
                "aren't installed. Train it with notebooks/02_train_distilbert.ipynb "
                "on Colab, unzip the result into backend/models/distilbert/, and "
                "run `pip install torch transformers`."
            )
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_DIR)
        _model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
        _model.to(_device)
        _model.eval()
    return _model, _tokenizer, _device


def predict_message(text: str) -> dict:
    """Classify a single message. Same return shape as ml/predict.py."""
    import torch

    model, tokenizer, device = _load()

    inputs = tokenizer(text, truncation=True, padding="max_length", max_length=64, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.softmax(logits, dim=-1)[0]

    pred_class = int(torch.argmax(probs).item())
    confidence = float(probs[pred_class].item())

    return {
        "label": CLASS_TO_LABEL[pred_class],
        "category": CLASS_TO_CATEGORY[pred_class],
        "confidence": round(confidence, 4),
        "model": "distilbert",
    }


if __name__ == "__main__":
    if not is_available():
        print(f"No model found at {MODEL_DIR} -- train it first (see notebooks/02_train_distilbert.ipynb).")
    else:
        examples = [
            "You're worthless, just disappear already.",
            "Great job on the presentation today!",
            "I know where you live, watch your back.",
        ]
        for ex in examples:
            print(ex, "->", predict_message(ex))
