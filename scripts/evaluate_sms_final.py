import os
import sys
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support

# Ensure backend in sys.path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.model_service import ModelService

def main():
    final_path = os.path.join(backend_dir, "data", "sms_final.tsv")
    if not os.path.exists(final_path):
        print(f"File not found: {final_path}")
        return

    mtime = os.path.getmtime(final_path)
    df = pd.read_csv(final_path, sep="\t", header=None, names=["label", "text"])
    print("=" * 60)
    print("SHIELDAI SMS SPAM EVALUATION ON HELD-OUT FINAL SPLIT")
    print(f"Dataset path: {final_path}")
    print(f"File rows: {len(df)}")
    print(f"Spam support: {sum(df['label'] == 'spam')}, Ham support: {sum(df['label'] == 'ham')}")
    print("=" * 60)

    ms = ModelService.get_instance()
    print(f"Model loaded: {ms.is_loaded}")

    y_true = []
    y_pred = []
    fps = []
    fns = []

    for idx, row in df.iterrows():
        text = str(row["text"])
        true_label = 1 if row["label"] == "spam" else 0
        y_true.append(true_label)

        res = ms.analyze(text)
        # An SMS is flagged by the engine if score >= 50.0
        is_flagged = 1 if res.get("score", 0.0) >= 50.0 else 0
        y_pred.append(is_flagged)

        if true_label == 0 and is_flagged == 1:
            fps.append({
                "index": idx,
                "text": text,
                "score": res.get("score", 0.0),
                "category": res.get("category_scores", {}),
                "signals": [s["signal"] for s in res.get("signals", [])]
            })
        elif true_label == 1 and is_flagged == 0:
            fns.append({
                "index": idx,
                "text": text,
                "score": res.get("score", 0.0),
                "category": res.get("category_scores", {}),
                "signals": [s["signal"] for s in res.get("signals", [])]
            })

    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", pos_label=1)
    cm = confusion_matrix(y_true, y_pred)
    # cm: [[TN, FP], [FN, TP]]
    tn, fp, fn, tp = cm.ravel()

    print("\n--- RESULTS ON HELD-OUT FINAL SET ---")
    print(f"True Negatives (Ham correct):  {tn}")
    print(f"False Positives (Ham flagged): {fp}")
    print(f"False Negatives (Spam missed): {fn}")
    print(f"True Positives (Spam caught):  {tp}")
    print(f"\nPrecision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")

    print("\nConfusion Matrix:")
    print(f"[[TN={tn}, FP={fp}],")
    print(f" [FN={fn}, TP={tp}]]")

    print(f"\nTotal False Positives: {len(fps)}")
    print("Top 10 False Positives:")
    for i, fp_item in enumerate(fps[:10]):
        print(f"  [{i+1}] Score: {fp_item['score']} | Text: {repr(fp_item['text'][:100])} | Signals: {fp_item['signals']}")

    print(f"\nTotal False Negatives: {len(fns)}")
    print("Sample False Negatives (First 10):")
    for i, fn_item in enumerate(fns[:10]):
        print(f"  [{i+1}] Score: {fn_item['score']} | Text: {repr(fn_item['text'][:100])}")

if __name__ == "__main__":
    main()

