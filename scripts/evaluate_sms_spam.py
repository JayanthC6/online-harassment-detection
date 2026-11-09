import os
import sys
import pandas as pd
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.model_service import ModelService

def main():
    tsv_path = os.path.join(BACKEND_DIR, "data", "sms_spam.tsv")
    if not os.path.exists(tsv_path):
        print(f"Dataset not found at {tsv_path}")
        return

    df = pd.read_csv(tsv_path, sep="\t", names=["label", "text"])
    row_count = len(df)
    print(f"Loaded UCI SMS Spam Collection with {row_count} messages.")
    print(df["label"].value_counts().to_dict())

    ms = ModelService.get_instance()

    y_true = (df["label"] == "spam").astype(int).values
    texts = df["text"].astype(str).tolist()

    fraud_flags = []
    false_positives = []
    false_negatives = []

    for idx, text in enumerate(texts):
        r_res = ms.evaluate_rules(text)
        r_cats = r_res["category_scores"]
        
        # Fraud rule flagged if scam >= 50.0 or phishing >= 50.0 or sextortion >= 50.0
        max_fraud = max(r_cats.get("scam", 0.0), r_cats.get("phishing", 0.0), r_cats.get("sextortion", 0.0))
        is_fraud = 1 if max_fraud >= 50.0 else 0
        fraud_flags.append(is_fraud)

        # Track FP and FN for fraud rules
        if y_true[idx] == 0 and is_fraud == 1:
            false_positives.append({
                "index": idx,
                "text": text,
                "max_score": max_fraud,
                "signals": [s["signal"] for s in r_res["signals"]]
            })
        elif y_true[idx] == 1 and is_fraud == 0:
            false_negatives.append({
                "index": idx,
                "text": text,
                "max_score": max_fraud,
                "signals": [s["signal"] for s in r_res["signals"]]
            })

    y_pred_fraud = np.array(fraud_flags)
    tp = int(np.sum((y_true == 1) & (y_pred_fraud == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred_fraud == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred_fraud == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred_fraud == 0)))

    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

    print("\n" + "=" * 82)
    print("INDEPENDENT EVALUATION: UCI SMS SPAM COLLECTION (FRAUD RULES LAYER)")
    print("=" * 82)
    print(f"Total Messages:        {row_count}")
    print(f"True Spam/Phishing:    {np.sum(y_true == 1)} ({np.sum(y_true == 1)/row_count:.1%})")
    print(f"True Ham (Legitimate): {np.sum(y_true == 0)} ({np.sum(y_true == 0)/row_count:.1%})")
    print("-" * 82)
    print(f"True Positives (TP):   {tp}")
    print(f"False Positives (FP):  {fp}")
    print(f"False Negatives (FN):  {fn}")
    print(f"True Negatives (TN):   {tn}")
    print("-" * 82)
    print(f"Precision:             {prec:.4f} ({prec*100:.2f}%)")
    print(f"Recall:                {rec:.4f} ({rec*100:.2f}%)")
    print(f"F1-Score:              {f1:.4f} ({f1*100:.2f}%)")
    print("=" * 82)

    print(f"\nTOP FALSE POSITIVES (Legitimate Ham messages flagged by Fraud Rules) [Total: {len(false_positives)}]:")
    print("-" * 82)
    for i, fp_item in enumerate(false_positives[:10]):
        print(f"[{i+1}] Row {fp_item['index']}: {fp_item['text']!r}")
        print(f"     Signals: {fp_item['signals']}")

    print(f"\nSAMPLE FALSE NEGATIVES (Spam messages missed by Fraud Rules) [Total: {len(false_negatives)}]:")
    print("-" * 82)
    for i, fn_item in enumerate(false_negatives[:10]):
        print(f"[{i+1}] Row {fn_item['index']}: {fn_item['text']!r}")
        print(f"     Signals: {fp_item['signals'] if 'signals' in fp_item else []}")

if __name__ == "__main__":
    main()
