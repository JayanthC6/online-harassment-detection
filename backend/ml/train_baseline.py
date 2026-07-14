"""
Trains the baseline classifier: TF-IDF features + Logistic Regression.

This is intentionally the SIMPLEST model in the project. It exists so you
always have a fast, working end-to-end pipeline while the heavier DistilBERT
model (train_transformer.py) trains separately. Compare both in your report.

Usage:
    python train_baseline.py
"""
import sys
import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

sys.path.append(os.path.dirname(__file__))
from preprocess import preprocess

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "davidson_hate_speech.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

# Davidson et al. label scheme -> our category names.
# class 0 = hate speech, class 1 = offensive language, class 2 = neither
CLASS_TO_CATEGORY = {
    0: "hate_speech",
    1: "offensive_language",
    2: "none",
}
CLASS_TO_LABEL = {
    0: "harassing",
    1: "harassing",
    2: "non_harassing",
}


def load_data():
    df = pd.read_csv(DATA_PATH)
    df["clean_text"] = df["tweet"].apply(preprocess)
    df = df[df["clean_text"].str.strip() != ""]  # drop rows that became empty
    return df


def train():
    print("Loading data...")
    df = load_data()
    print(f"  {len(df)} usable rows after cleaning")

    X = df["clean_text"]
    y = df["class"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Vectorizing (TF-IDF, unigrams + bigrams, top 10k features)...")
    vectorizer = TfidfVectorizer(max_features=10_000, ngram_range=(1, 2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    print("Training Logistic Regression...")
    # class_weight="balanced" matters here: hate_speech is ~13x rarer than
    # offensive_language in this dataset, so an unweighted model mostly
    # predicts the majority class and looks falsely accurate.
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(X_train_vec, y_train)

    y_pred = clf.predict(X_test_vec)
    print("\n=== Classification report (test set) ===")
    print(classification_report(
        y_test, y_pred,
        target_names=["hate_speech", "offensive_language", "none"]
    ))
    print("=== Confusion matrix ===")
    print(confusion_matrix(y_test, y_pred))

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(clf, os.path.join(MODEL_DIR, "baseline_clf.joblib"))
    joblib.dump(vectorizer, os.path.join(MODEL_DIR, "baseline_vectorizer.joblib"))
    print(f"\nSaved model + vectorizer to {MODEL_DIR}/")


if __name__ == "__main__":
    train()
