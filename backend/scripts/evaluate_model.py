"""
ShieldAI Model Evaluation Script.
Reads backend/data/test.csv and computes per-label Precision, Recall, F1,
and 2x2 Confusion Matrices using calibrated thresholds.
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np

# Ensure backend directory is in PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.model_service import ModelService, LABEL_ORDER

DEFAULT_CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "test.csv"))

SAMPLE_TEST_DATA = [
    {
        "text": "I know where you live and I am going to find and kill you.",
        "Hate Speech": 0, "Cyberbullying / Harassment": 0, "Threat": 1,
        "Toxicity / Offensive Language": 1, "Profanity": 0, "Clean": 0
    },
    {
        "text": "You are a stupid idiot, nobody likes you and you should disappear.",
        "Hate Speech": 0, "Cyberbullying / Harassment": 1, "Threat": 0,
        "Toxicity / Offensive Language": 1, "Profanity": 0, "Clean": 0
    },
    {
        "text": "Go back to your country, you dirty foreigners do not belong here.",
        "Hate Speech": 1, "Cyberbullying / Harassment": 1, "Threat": 0,
        "Toxicity / Offensive Language": 1, "Profanity": 0, "Clean": 0
    },
    {
        "text": "What the fuck is this bullshit shut your damn mouth.",
        "Hate Speech": 0, "Cyberbullying / Harassment": 0, "Threat": 0,
        "Toxicity / Offensive Language": 1, "Profanity": 1, "Clean": 0
    },
    {
        "text": "Hey, do you want to grab lunch together at the cafeteria today?",
        "Hate Speech": 0, "Cyberbullying / Harassment": 0, "Threat": 0,
        "Toxicity / Offensive Language": 0, "Profanity": 0, "Clean": 1
    },
    {
        "text": "The presentation on machine learning was very informative and well structured.",
        "Hate Speech": 0, "Cyberbullying / Harassment": 0, "Threat": 0,
        "Toxicity / Offensive Language": 0, "Profanity": 0, "Clean": 1
    },
    {
        "text": "Watch your back after school, I will beat you till you bleed.",
        "Hate Speech": 0, "Cyberbullying / Harassment": 1, "Threat": 1,
        "Toxicity / Offensive Language": 1, "Profanity": 0, "Clean": 0
    },
    {
        "text": "You disgusting subhuman piece of trash, drop dead.",
        "Hate Speech": 0, "Cyberbullying / Harassment": 1, "Threat": 0,
        "Toxicity / Offensive Language": 1, "Profanity": 1, "Clean": 0
    },
    {
        "text": "Please review the attached quarterly financial report and let me know your thoughts.",
        "Hate Speech": 0, "Cyberbullying / Harassment": 0, "Threat": 0,
        "Toxicity / Offensive Language": 0, "Profanity": 0, "Clean": 1
    },
    {
        "text": "All people of that religion are evil and must be eliminated from society.",
        "Hate Speech": 1, "Cyberbullying / Harassment": 0, "Threat": 1,
        "Toxicity / Offensive Language": 1, "Profanity": 0, "Clean": 0
    }
]


def ensure_sample_csv(path: str):
    """Generates a starter test.csv if none exists."""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df_sample = pd.DataFrame(SAMPLE_TEST_DATA)
        df_sample.to_csv(path, index=False)
        print(f"[INFO] Created reference test dataset at: {path}")


def evaluate(csv_path: str, batch_size: int = 16):
    print("=" * 78)
    print("SHIELDAI DISTILBERT MULTI-LABEL EVALUATION REPORT")
    print("=" * 78)
    print(f"Dataset path: {csv_path}")

    if not os.path.exists(csv_path):
        ensure_sample_csv(csv_path)

    df = pd.read_csv(csv_path)
    print(f"Total rows loaded: {len(df)}")

    # Verify column structure
    required_cols = ["text"] + LABEL_ORDER
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"CSV is missing required columns: {missing_cols}\n"
            f"Expected schema: 'text', {', '.join(LABEL_ORDER)}"
        )

    # Initialize model service
    service = ModelService.get_instance()
    if not service.is_loaded:
        print("[WARNING] DistilBERT model is not loaded. Cannot run neural evaluation.")
        return

    texts = df["text"].astype(str).tolist()
    y_true = df[LABEL_ORDER].astype(int).values

    print("\nRunning inference with calibrated thresholds:")
    for label in LABEL_ORDER:
        t = service.thresholds.get(label, 0.5)
        print(f"  • {label:30s} threshold = {t:.4f}")

    # Batched inference
    y_pred_list = []
    y_prob_list = []

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_res = service._predict_model_batch(batch_texts)

        for res in batch_res:
            probs = [res["probs"].get(l, 0.0) for l in LABEL_ORDER]
            thresholds = [service.thresholds.get(l, 0.5) for l in LABEL_ORDER]
            preds = [1 if p >= t else 0 for p, t in zip(probs, thresholds)]

            y_prob_list.append(probs)
            y_pred_list.append(preds)

    y_pred = np.array(y_pred_list)

    # Compute metrics per label
    print("\n" + "-" * 78)
    print(f"{'Label':<32} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<8}")
    print("-" * 78)

    precisions = []
    recalls = []
    f1s = []
    cms = {}

    for idx, label in enumerate(LABEL_ORDER):
        yt = y_true[:, idx]
        yp = y_pred[:, idx]

        tp = int(np.sum((yt == 1) & (yp == 1)))
        fp = int(np.sum((yt == 0) & (yp == 1)))
        fn = int(np.sum((yt == 1) & (yp == 0)))
        tn = int(np.sum((yt == 0) & (yp == 0)))

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        support = int(np.sum(yt == 1))

        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)
        cms[label] = [[tn, fp], [fn, tp]]

        print(f"{label:<32} {prec:<12.4f} {rec:<12.4f} {f1:<12.4f} {support:<8}")

    macro_f1 = np.mean(f1s)
    micro_tp = np.sum((y_true == 1) & (y_pred == 1))
    micro_fp = np.sum((y_true == 0) & (y_pred == 1))
    micro_fn = np.sum((y_true == 1) & (y_pred == 0))
    micro_prec = micro_tp / (micro_tp + micro_fp) if (micro_tp + micro_fp) > 0 else 0.0
    micro_rec = micro_tp / (micro_tp + micro_fn) if (micro_tp + micro_fn) > 0 else 0.0
    micro_f1 = (2 * micro_prec * micro_rec) / (micro_prec + micro_rec) if (micro_prec + micro_rec) > 0 else 0.0

    print("-" * 78)
    print(f"{'Macro Average':<32} {np.mean(precisions):<12.4f} {np.mean(recalls):<12.4f} {macro_f1:<12.4f} {int(np.sum(y_true)):<8}")
    print(f"{'Micro Average':<32} {micro_prec:<12.4f} {micro_rec:<12.4f} {micro_f1:<12.4f} {int(np.sum(y_true)):<8}")
    print("=" * 78)

    # Print 2x2 Confusion Matrices
    print("\nPER-LABEL 2x2 CONFUSION MATRICES (Format: [[TN, FP], [FN, TP]]):")
    print("-" * 78)
    for label in LABEL_ORDER:
        cm = cms[label]
        print(f"\nLabel: {label}")
        print(f"  Predicted 0 (Neg)  Predicted 1 (Pos)")
        print(f"Actual 0:    TN = {cm[0][0]:<6}    FP = {cm[0][1]:<6}")
        print(f"Actual 1:    FN = {cm[1][0]:<6}    TP = {cm[1][1]:<6}")

    print("\n" + "=" * 78)
    print("Evaluation completed successfully.")
    print("=" * 78)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate ShieldAI DistilBERT Model on test.csv")
    parser.add_argument("--csv", default=DEFAULT_CSV_PATH, help="Path to test.csv")
    parser.add_argument("--batch-size", default=16, type=int, help="Batch size for inference")
    args = parser.parse_args()

    evaluate(args.csv, args.batch_size)

