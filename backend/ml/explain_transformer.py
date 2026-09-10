"""
Token-level explainability for the fine-tuned DistilBERT multi-label model
using Captum's LayerIntegratedGradients (LIG).

Design constraints:
  - ONLY produces attributions for labels the neural model was trained on.
    Symbolic-only categories (Scam, Phishing, Extortion, etc.) are deliberately
    excluded — gradient attribution against a concept the model has no logit for
    would produce meaningless noise, not a real explanation.
  - Attributions are SIGNED: positive means the token pushed the model TOWARD
    the label, negative means it pushed AWAY. These are returned separately so
    the frontend can render them with distinct visual encoding.
  - Never called synchronously during /predict. Invoked only from /predict/explain.
"""

import os
import re

# ── Labels the neural model was trained on (from predict_transformer.py id2label) ──
NEURAL_LABELS = {
    "Hate Speech",
    "Cyberbullying / Harassment",
    "Threat",
    "Toxicity / Offensive Language",
    "Profanity",
    "Clean",
}

# Labels that come ONLY from the rule/heuristic engine — never attempt IG on these
SYMBOLIC_ONLY_LABELS = {
    "Scam",
    "Phishing",
    "Extortion",
    "Blackmail",
    "Fraud",
    "Impersonation",
    "Social Engineering",
    "Identity Attack",
    "Spam",
    "Self Harm",
}


def is_neural_label(label: str) -> bool:
    """Return True if this label has a dedicated logit in the neural model."""
    return label in NEURAL_LABELS


# ── Lazy singletons — loaded only on first /predict/explain call ──
_model = None
_tokenizer = None
_device = None
_id2label = None


def _load():
    """Load the model/tokenizer once and cache. Thread-safe enough for dev/single-worker Flask."""
    global _model, _tokenizer, _device, _id2label
    if _model is not None:
        return _model, _tokenizer, _device, _id2label

    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    token = os.getenv("HF_TOKEN")
    repo = "Jayant62003/shieldai-distilbert-multilabel"
    _device = torch.device("cpu")  # IG is memory-intensive; CPU is safer for inference
    _tokenizer = AutoTokenizer.from_pretrained(repo, token=token)
    _model = AutoModelForSequenceClassification.from_pretrained(repo, token=token)
    _model.to(_device)
    _model.eval()

    # Resolve id2label (some models export LABEL_0 instead of string names)
    raw = _model.config.id2label or {}
    if raw and "LABEL_0" in raw.values():
        _id2label = {
            0: "Hate Speech",
            1: "Cyberbullying / Harassment",
            2: "Threat",
            3: "Toxicity / Offensive Language",
            4: "Profanity",
            5: "Clean",
        }
    else:
        _id2label = {int(k): v for k, v in raw.items()}

    return _model, _tokenizer, _device, _id2label


def _label_to_index(label: str, id2label: dict) -> int:
    """Map a string label to its logit index in the model."""
    for idx, name in id2label.items():
        if name == label:
            return idx
    raise ValueError(f"Label '{label}' not found in model id2label: {id2label}")


def _merge_subword_tokens(tokens: list, scores: list) -> list:
    """
    Merge WordPiece subword tokens (those starting with '##') into the root word,
    summing their attribution scores. Returns [{token, score}].
    """
    merged = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        score = scores[i]
        # Accumulate subsequent subword pieces
        while i + 1 < len(tokens) and tokens[i + 1].startswith("##"):
            i += 1
            tok = tok + tokens[i][2:]  # strip the ## prefix
            score += scores[i]
        merged.append({"token": tok, "raw_score": float(score)})
        i += 1
    return merged


def compute_ig_attributions(text: str, label: str, n_steps: int = 50) -> dict:
    """
    Compute Layer Integrated Gradients attributions for `label` over `text`.

    Args:
        text:    The raw input string.
        label:   One of the NEURAL_LABELS strings.
        n_steps: IG approximation steps (50 is fast; 200 is more accurate but slower).

    Returns:
        {
            "label":  str,
            "method": "captum_lig",
            "tokens": [
                {"token": str, "score": float, "sign": "positive"|"negative"|"neutral"}
            ]
        }

    The `score` field is the absolute attribution magnitude, normalized to [0, 1].
    Use `sign` to determine rendering color: positive = pushed toward label,
    negative = pushed away.

    Raises:
        RuntimeError if HF_TOKEN is missing or model can't be loaded.
        ValueError  if `label` is not a neural label.
    """
    if not is_neural_label(label):
        raise ValueError(
            f"'{label}' is a symbolic-only category. "
            "IG attribution is only meaningful for neural-trained labels."
        )

    if not os.getenv("HF_TOKEN"):
        raise RuntimeError("HF_TOKEN is not set — cannot load the neural model.")

    import torch
    from captum.attr import IntegratedGradients

    model, tokenizer, device, id2label = _load()
    label_idx = _label_to_index(label, id2label)

    # ── Tokenize ──
    encoding = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=256,
        padding="max_length",
    )
    input_ids = encoding["input_ids"].to(device)
    attention_mask = encoding["attention_mask"].to(device)

    # ── Baseline: all-[PAD] token ids (standard IG baseline for text) ──
    pad_id = tokenizer.pad_token_id
    baseline_ids = torch.full_like(input_ids, pad_id)

    # ── Define forward function for IG ──
    # Instead of using LayerIntegratedGradients which can cause shape mismatches due to hooks,
    # we use standard IntegratedGradients and provide inputs_embeds directly.
    def forward_func(inputs_embeds_):
        batch = inputs_embeds_.shape[0]
        mask = attention_mask.expand(batch, -1)
        outputs = model(inputs_embeds=inputs_embeds_, attention_mask=mask)
        return torch.sigmoid(outputs.logits[:, label_idx])

    # Compute actual embeddings for inputs and baselines
    inputs_embeds = model.distilbert.embeddings(input_ids)
    baseline_embeds = model.distilbert.embeddings(baseline_ids)

    # We must lock this section so concurrent requests don't capture each other's activations.
    import threading
    if not hasattr(compute_ig_attributions, "_ig_lock"):
        compute_ig_attributions._ig_lock = threading.Lock()

    with compute_ig_attributions._ig_lock:
        ig = IntegratedGradients(forward_func)
        
        # Attribute directly on the embeddings
        attributions, delta = ig.attribute(
            inputs=inputs_embeds,
            baselines=baseline_embeds,
            target=None,
            n_steps=n_steps,
            internal_batch_size=8,
            return_convergence_delta=True
        )
    # attributions: (1, seq_len, embed_dim=768) — sum across embed dim → per-token scalar
    attr_scores = attributions.sum(dim=-1).squeeze(0)  # shape: (seq_len,)

    # ── Decode tokens ──
    token_ids_list = input_ids[0].tolist()
    tokens_raw = tokenizer.convert_ids_to_tokens(token_ids_list)
    scores_raw = attr_scores.detach().tolist()

    # ── Filter special + padding tokens ──
    skip = {tokenizer.cls_token, tokenizer.sep_token, tokenizer.pad_token, "[CLS]", "[SEP]", "[PAD]"}
    filtered_tokens = []
    filtered_scores = []
    for tok, sc, tid in zip(tokens_raw, scores_raw, token_ids_list):
        if tok in skip or tid == pad_id:
            continue
        filtered_tokens.append(tok)
        filtered_scores.append(sc)

    # ── Merge subword pieces ──
    merged = _merge_subword_tokens(filtered_tokens, filtered_scores)

    # ── Normalize scores to [-1, 1] ──
    raw_scores = [m["raw_score"] for m in merged]
    max_abs = max((abs(s) for s in raw_scores), default=1.0) or 1.0

    result_tokens = []
    for m in merged:
        norm = m["raw_score"] / max_abs  # in [-1, 1]
        sign = "positive" if norm > 0.05 else ("negative" if norm < -0.05 else "neutral")
        result_tokens.append({
            "token": m["token"],
            "score": round(abs(norm), 4),   # magnitude
            "sign": sign,                    # direction
            "raw": round(m["raw_score"], 6), # for debugging
        })

    convergence = float(delta.mean().abs().item()) if delta is not None else None

    return {
        "label": label,
        "method": "captum_lig",
        "n_steps": n_steps,
        "convergence_delta": convergence,
        "tokens": result_tokens,
    }
