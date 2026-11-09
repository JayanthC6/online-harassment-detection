import os
import sys
import csv

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from services.model_service import ModelService

def main():
    csv_path = os.path.join(BACKEND_DIR, "data", "fraud_cases.csv")
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} fraud benchmark cases from backend/data/fraud_cases.csv")

    ms = ModelService.get_instance()

    tp, fp, fn, tn = 0, 0, 0, 0
    discrepancies = []

    for r in rows:
        text = r["text"]
        exp_flagged = int(r["expected_flagged"])
        exp_label = r["expected_label"]
        case_id = r["id"]
        category_type = r["category_type"]

        res = ms.analyze(text)
        act_score = res["score"]
        act_level = res["level"]
        cat_scores = res["category_scores"]

        # Fraud/threat flagged if score >= 50 or level in ["medium", "high", "critical"] with scam/phish/threat active
        is_fraud_flagged = (
            cat_scores.get("scam", 0) >= 50.0 or
            cat_scores.get("phishing", 0) >= 50.0 or
            cat_scores.get("sextortion", 0) >= 50.0 or
            cat_scores.get("threat", 0) >= 50.0 or
            act_score >= 50.0
        )
        act_flagged = 1 if is_fraud_flagged else 0

        if exp_flagged == 1 and act_flagged == 1:
            tp += 1
        elif exp_flagged == 0 and act_flagged == 1:
            fp += 1
            discrepancies.append({
                "id": case_id,
                "type": category_type,
                "text": text,
                "expected": "CLEAN / UNFLAGGED",
                "actual": f"FLAGGED ({act_level}, score: {act_score})",
                "signals": [s["signal"] for s in res.get("signals", [])]
            })
        elif exp_flagged == 1 and act_flagged == 0:
            fn += 1
            discrepancies.append({
                "id": case_id,
                "type": category_type,
                "text": text,
                "expected": f"FLAGGED ({exp_label})",
                "actual": f"CLEAN / MISSED ({act_level}, score: {act_score})",
                "signals": [s["signal"] for s in res.get("signals", [])]
            })
        else:
            tn += 1

    total = len(rows)
    acc = (tp + tn) / total
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

    print("\n" + "=" * 82)
    print("INDEPENDENT BENCHMARK: 45 INDIAN FRAUD, PHISHING, OTP & CHAT CASES")
    print("=" * 82)
    print(f"Total Cases:          {total}")
    print(f"True Fraud/Threats:   {tp + fn}")
    print(f"True Legitimate:      {tn + fp}")
    print("-" * 82)
    print(f"Accuracy:             {tp + tn}/{total} ({acc:.1%})")
    print(f"True Positives (TP):  {tp}")
    print(f"False Positives (FP): {fp}")
    print(f"False Negatives (FN): {fn}")
    print(f"True Negatives (TN):  {tn}")
    print("-" * 82)
    print(f"Precision:            {prec:.4f} ({prec*100:.2f}%)")
    print(f"Recall:               {rec:.4f} ({rec*100:.2f}%)")
    print(f"F1-Score:             {f1:.4f} ({f1*100:.2f}%)")
    print("=" * 82)

    if discrepancies:
        print(f"\nDISCREPANCIES / ERRORS ({len(discrepancies)} cases):")
        print("-" * 82)
        for d in discrepancies:
            print(f"[{d['id']}] ({d['type']}): {d['text']!r}")
            print(f"     Expected: {d['expected']} | Actual: {d['actual']}")
            print(f"     Signals:  {d['signals']}")
    else:
        print("\nAll 45 cases passed with 100% accuracy (0 False Positives, 0 False Negatives)!")

if __name__ == "__main__":
    main()

