import csv
import os
import sys
import json

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(base_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.model_service import ModelService

def run_hard_cases():
    svc = ModelService.get_instance()
    csv_path = os.path.join(backend_dir, "data", "hard_cases.csv")
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} cases from {csv_path}\n" + "="*80)
    
    passes = []
    discrepancies = []

    for r in rows:
        case_id = r["id"]
        c_type = r["case_type"]
        text = r["text"]
        exp_level = r["expected_level"]
        exp_cat = r["expected_category"]
        notes = r["notes"]

        result = svc.analyze(text)
        act_level = result["level"]
        act_score = result["score"]
        act_cats = result["category_scores"]
        
        # Primary category is the highest scoring category
        # If score is low (< 35), category is effectively 'clean'
        if act_score < 35.0:
            act_cat = "clean"
        else:
            act_cat = max(act_cats, key=act_cats.get)

        # Match check
        level_match = (act_level == exp_level)
        cat_match = (exp_cat == "clean" and act_score < 35.0) or (exp_cat == act_cat) or (exp_cat in ["harassment", "abusive_language"] and act_cat in ["harassment", "abusive_language"])

        status = "PASS" if (level_match and cat_match) else "MISMATCH"
        case_summary = {
            "id": case_id,
            "type": c_type,
            "text": text[:60] + "..." if len(text) > 60 else text,
            "expected": f"{exp_level}/{exp_cat}",
            "actual": f"{act_level}/{act_cat} (score: {act_score:.1f})",
            "status": status,
            "notes": notes,
            "signals": [s["signal"] for s in result.get("signals", [])]
        }

        if status == "PASS":
            passes.append(case_summary)
            print(f"[PASS] #{case_id} [{c_type}]: exp={exp_level}/{exp_cat} -> act={act_level}/{act_cat} ({act_score:.1f})")
        else:
            discrepancies.append(case_summary)
            print(f"[FAIL/WEAKNESS] #{case_id} [{c_type}]: exp={exp_level}/{exp_cat} -> act={act_level}/{act_cat} ({act_score:.1f}) | Signals: {case_summary['signals']}")

    print("\n" + "="*80)
    print(f"SUMMARY: {len(passes)}/{len(rows)} Passed, {len(discrepancies)} Discrepancies/Failures")
    print("="*80)

    # Save summary to file for documentation
    out_json = os.path.join(backend_dir, "data", "hard_cases_results.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "total": len(rows),
            "passed": len(passes),
            "discrepancies": len(discrepancies),
            "passes": passes,
            "discrepancies": discrepancies
        }, f, indent=2)
    print(f"Detailed results saved to {out_json}")

if __name__ == "__main__":
    run_hard_cases()

