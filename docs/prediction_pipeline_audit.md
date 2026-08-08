# Prediction Pipeline Forensic Audit

## Exact Request Text
`"Everyone laughs at you because you're completely useless. Just disappear already."`

## 1. Live Backend Response
```json
{
  "label": "Safe",
  "category": "Clean",
  "confidence": 0.97,
  "primary_label": "Clean",
  "secondary_labels": {},
  "risk_score": 5.0,
  "model": "distilbert+multi_label_heuristics"
}
```

## 2. Raw DistilBERT Inference
The underlying `distilbert-base-uncased` model evaluates the text. Because it lacks explicit slurs or keywords it was trained on, it fails to recognize the implicit bullying and returns:
```json
{
  "label": "non_harassing",
  "category": "none",
  "confidence": 0.97,
  "model": "distilbert"
}
```

## 3. PrimaryModelAdapter Output
The base adapter maps the raw model output into the standard schema:
```json
{
  "primary_label": "Clean",
  "confidence": 0.97,
  "secondary_labels": {},
  "label": "non_harassing",
  "category": "none",
  "model": "distilbert"
}
```

## 4. HeuristicMultiLabelAdapter Output
The heuristic layer scans the text for specific regex patterns:
- `Cyberbullying` checks for: `\b(loser|worthless|ugly|fat|stupid|idiot|dumb|kys|die)\b`
- The input uses the word `"useless"`, which is **not** in the regex list.
- The input uses `"disappear already"`, which is **not** in the regex list.
- Because no patterns match, `secondary_labels` is empty `{}`.
- The override condition `if result["primary_label"] == "Clean" and filtered_secondary:` evaluates to `False`.
- The adapter returns the prediction completely unchanged.

## 5. Execution Path & Root Cause Analysis

### Execution Path
1. `routes_public.py` -> `predict_message_api`
2. `PredictionService.classify_text()`
3. `HeuristicMultiLabelAdapter.predict()`
4. `PrimaryModelAdapter.predict()`
5. `predict_transformer.predict_message()`

### Root Cause Identified
1. **DistilBERT Failure (False Negative):** The primary ML model fails to detect implicit psychological abuse that lacks explicit profanity or known training slurs.
2. **Heuristic Miss:** The static heuristic patterns are rigid. They look for `"worthless"` but miss `"useless"`. They look for `"kill yourself"` but miss `"disappear already"`. Because regex is brittle, the heuristic engine fails to act as a safety net for this specific phrasing.
3. **Resulting State:** Both the primary AI model and the secondary regex layer fail to flag the message. The system defaults to the primary model's "Safe" classification with its original 97% confidence.

### Exact Files and Functions Responsible
- **Model Layer:** `backend/ml/predict_transformer.py` (`predict_message`) - The model is under-trained for zero-shot or implicit abuse.
- **Heuristics Layer:** `backend/ml/adapters/heuristic.py` (`HeuristicMultiLabelAdapter.__init__`) - The hardcoded regex patterns are too brittle to catch variations of abusive phrases.

### Recommended Fix
Do **NOT** simply add `"useless"` or `"disappear"` to the regex array. This is a game of whack-a-mole that will continuously fail against new variations.

To solve the root cause permanently without changing the frontend or breaking backward compatibility:
1. **Upgrade the Primary Engine:** We should replace the local DistilBERT inference with a more powerful Context-Aware LLM (e.g., using a prompt-based zero-shot classifier) that understands implicit context, psychological abuse, and nuanced threats.
2. **Preserve the Architecture:** The LLM can be wrapped in a new adapter (e.g., `LLMPrimaryAdapter`) that perfectly mimics `PrimaryModelAdapter`, maintaining all API contracts and the heuristic layer.
