"""
Loads the fine-tuned DistilBERT multi-label model from the Hugging Face Hub
and classifies new messages.

Imports for torch/transformers are deliberately lazy (inside functions, not
at module top level) so that importing this module doesn't crash the whole
Flask app on machines that haven't installed those libraries yet.
"""
import os
import json

MODEL_REPO = "Jayant62003/shieldai-distilbert-multilabel"

_model = None
_tokenizer = None
_thresholds = None
_device = None


def is_available() -> bool:
    """Check whether we have HF_TOKEN to load the model."""
    if not os.getenv("HF_TOKEN"):
        print("DEBUG: is_available returning False because HF_TOKEN is not set.")
        return False
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except (ImportError, OSError) as e:
        print(f"DEBUG: is_available returning False because import failed: {e}")
        return False
    return True


def _load():
    global _model, _tokenizer, _thresholds, _device
    if _model is None:
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        from huggingface_hub import hf_hub_download

        if not is_available():
            raise ValueError("HF_TOKEN environment variable is missing or torch/transformers are not installed.")
        
        token = os.getenv("HF_TOKEN")
        
        # Load thresholds.json
        thresholds_path = hf_hub_download(repo_id=MODEL_REPO, filename="thresholds.json", token=token)
        with open(thresholds_path, "r") as f:
            _thresholds = json.load(f)
            
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_REPO, token=token)
        _model = AutoModelForSequenceClassification.from_pretrained(MODEL_REPO, token=token)
        _model.to(_device)
        _model.eval()
    return _model, _tokenizer, _thresholds, _device


def predict_message(text: str) -> dict:
    """Classify a single message. Returns a multi-label output dictionary."""
    import torch

    model, tokenizer, thresholds, device = _load()

    inputs = tokenizer(text, truncation=True, padding="max_length", max_length=256, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = torch.sigmoid(logits)[0].cpu().numpy()

    # thresholds dict maps "Label Name" -> threshold float
    # We need to map model.config.id2label to the probability
    id2label = model.config.id2label
    # If the model config doesn't have the string names, map them manually
    if id2label and "LABEL_0" in id2label.values():
        id2label = {
            0: "Hate Speech",
            1: "Cyberbullying / Harassment",
            2: "Threat",
            3: "Toxicity / Offensive Language",
            4: "Profanity",
            5: "Clean"
        }
        
    neural_probs = {}
    
    for i, prob in enumerate(probs):
        label_name = id2label[i]
        neural_probs[label_name] = float(prob)
        
    return {
        "neural_probs": neural_probs,
        "thresholds": thresholds,
        "model": "distilbert"
    }


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
    
    if not is_available():
        print(f"HF_TOKEN missing or libraries missing.")
    else:
        examples = [
            "You're worthless, just disappear from here you fucker asshole",
            "Great job on the presentation today!",
            "I know where you live, I will kill you.",
        ]
        for ex in examples:
            print(ex)
            print(predict_message(ex))
            print()
