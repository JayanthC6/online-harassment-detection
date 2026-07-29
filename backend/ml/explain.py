"""
Word-level explainability for the baseline (TF-IDF + Logistic Regression) model.

Because the baseline is a linear model, we can compute the *exact* contribution
of each word to the predicted class:  contribution = tfidf_weight × class_coefficient.
This is not an approximation (like SHAP or LIME) — it's the literal arithmetic the
model performs internally, just surfaced for the user.

Only works for the baseline model.  For DistilBERT or toxic-bert (non-linear),
do NOT attempt a fake/approximate explanation — the caller should omit the field
and let the frontend show "not available for this model" instead.
"""
import os
import sys
import numpy as np
import joblib

sys.path.append(os.path.dirname(__file__))
from preprocess import preprocess

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

_clf = None
_vectorizer = None


def _load():
    global _clf, _vectorizer
    if _clf is None:
        clf_path = os.path.join(MODEL_DIR, "baseline_clf.joblib")
        vec_path = os.path.join(MODEL_DIR, "baseline_vectorizer.joblib")
        if not (os.path.exists(clf_path) and os.path.exists(vec_path)):
            return None, None
        _clf = joblib.load(clf_path)
        _vectorizer = joblib.load(vec_path)
    return _clf, _vectorizer


def explain_prediction(text: str, predicted_class: int, top_n: int = 5) -> list:
    """
    Compute exact word-level contributions to the predicted class.

    For each word in the input that appears in the TF-IDF vocabulary:
        contribution = tfidf_weight_for_that_word × model_coefficient_for_that_word_in_predicted_class

    Returns the top N words with POSITIVE contributions (i.e. words that
    pushed the model *toward* the predicted class), sorted descending.

    Args:
        text: raw input text (will be preprocessed internally)
        predicted_class: integer class index (0=hate_speech, 1=offensive_language, 2=none)
        top_n: how many top contributing words to return

    Returns:
        list of {"word": str, "contribution": float}, sorted descending by contribution.
        Empty list if the model isn't loaded or no words contributed positively.
    """
    clf, vectorizer = _load()
    if clf is None or vectorizer is None:
        return []

    cleaned = preprocess(text)
    if not cleaned:
        return []

    # Transform the text to get TF-IDF weights
    X = vectorizer.transform([cleaned])

    # Get the model coefficients for the predicted class
    # clf.coef_ shape: (n_classes, n_features) for multi-class
    coefficients = clf.coef_[predicted_class]

    # Get the feature names (vocabulary words)
    feature_names = vectorizer.get_feature_names_out()

    # Get the non-zero TF-IDF values for this text
    nonzero_indices = X.nonzero()[1]

    contributions = []
    for idx in nonzero_indices:
        tfidf_weight = X[0, idx]
        coef = coefficients[idx]
        contribution = float(tfidf_weight * coef)

        # Only keep positive contributions (words pushing toward this class)
        if contribution > 0:
            contributions.append({
                "word": feature_names[idx],
                "contribution": round(contribution, 4),
            })

    # Sort by contribution descending, take top N
    contributions.sort(key=lambda x: x["contribution"], reverse=True)
    return contributions[:top_n]


if __name__ == "__main__":
    CLASS_NAMES = {0: "hate_speech", 1: "offensive_language", 2: "none"}

    test_cases = [
        "You're worthless, just disappear already",
        "I hate all people from that country, they are all subhuman",
        "Great job on the presentation today!",
    ]

    clf, vectorizer = _load()
    if clf is None:
        print("Model not found. Run train_baseline.py first.")
    else:
        for text in test_cases:
            cleaned = preprocess(text)
            X = vectorizer.transform([cleaned])
            pred_class = int(clf.predict(X)[0])
            print(f"\nText: \"{text}\"")
            print(f"Predicted: {CLASS_NAMES[pred_class]} (class {pred_class})")
            explanation = explain_prediction(text, pred_class)
            if explanation:
                print("Top contributing words:")
                for item in explanation:
                    print(f"  {item['word']:20s} → {item['contribution']:.4f}")
            else:
                print("  (no positive contributions found)")
