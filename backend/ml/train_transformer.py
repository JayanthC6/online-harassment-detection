"""
Fine-tunes DistilBERT on the same Davidson et al. dataset used for the
baseline model, for direct comparison.

IMPORTANT: This needs a GPU to run in reasonable time. On CPU, fine-tuning
transformers takes hours instead of minutes. Use notebooks/02_train_distilbert.ipynb
on Google Colab (free T4 GPU) unless you have a local GPU.

This script was written against the standard HuggingFace Trainer API but
could NOT be executed in the dev sandbox that built the rest of this repo
(no access to huggingface.co there to download the pretrained weights).
Test it yourself the first time you run it — don't assume it's bug-free
the way train_baseline.py is, since that one WAS run and verified.

Usage:
    python train_transformer.py
"""
import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

import torch
from datasets import Dataset
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments,
)

sys.path.append(os.path.dirname(__file__))
from preprocess import clean_text  # lighter cleaning; BERT wants punctuation/case kept mostly intact

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw", "davidson_hate_speech.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "distilbert")
BASE_MODEL = "distilbert-base-uncased"

CLASS_NAMES = ["hate_speech", "offensive_language", "none"]


def load_data():
    df = pd.read_csv(DATA_PATH)
    # Unlike the TF-IDF baseline, transformers work better with lighter
    # cleaning -- keep case and punctuation, just strip URLs/mentions/RT.
    df["text"] = df["tweet"].apply(lambda t: clean_text(t))
    df = df[df["text"].str.strip() != ""]
    return df


def tokenize_dataset(df, tokenizer):
    ds = Dataset.from_pandas(df[["text", "class"]].rename(columns={"class": "label"}))
    return ds.map(
        lambda batch: tokenizer(batch["text"], truncation=True, padding="max_length", max_length=64),
        batched=True,
    )


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    report = classification_report(labels, preds, target_names=CLASS_NAMES, output_dict=True)
    return {
        "accuracy": report["accuracy"],
        "hate_speech_f1": report["hate_speech"]["f1-score"],
        "macro_f1": report["macro avg"]["f1-score"],
    }


def train():
    print("Loading data...")
    df = load_data()
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["class"])
    print(f"  train: {len(train_df)}  test: {len(test_df)}")

    print(f"Loading tokenizer + model ({BASE_MODEL})...")
    tokenizer = DistilBertTokenizerFast.from_pretrained(BASE_MODEL)
    model = DistilBertForSequenceClassification.from_pretrained(BASE_MODEL, num_labels=3)

    print("Tokenizing...")
    train_ds = tokenize_dataset(train_df, tokenizer)
    test_ds = tokenize_dataset(test_df, tokenizer)

    args = TrainingArguments(
        output_dir=os.path.join(MODEL_DIR, "checkpoints"),
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        logging_steps=50,
        fp16=torch.cuda.is_available(),  # only if a GPU is actually present
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=test_ds,
        compute_metrics=compute_metrics,
    )

    print("Training (this needs a GPU -- expect hours on CPU)...")
    trainer.train()

    print("\n=== Final evaluation ===")
    preds = trainer.predict(test_ds)
    y_pred = np.argmax(preds.predictions, axis=-1)
    y_true = test_df["class"].values
    print(classification_report(y_true, y_pred, target_names=CLASS_NAMES))
    print(confusion_matrix(y_true, y_pred))
    print("\nCompare this classification report against train_baseline.py's output")
    print("(saved model/models/README.md if you logged it) -- the number that")
    print("matters most is hate_speech precision/recall, since that's where")
    print("the baseline was weakest (32% precision).")

    os.makedirs(MODEL_DIR, exist_ok=True)
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    print(f"\nSaved model + tokenizer to {MODEL_DIR}/")


if __name__ == "__main__":
    train()
