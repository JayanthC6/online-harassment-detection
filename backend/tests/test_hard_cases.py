"""
Automated regression audit for hard_cases benchmark (Item 7).
Ensures expected labels are never mutated and tracks behavior on rows 14, 17, 18, 31.
"""
import os
import csv
import pytest
from services.model_service import ModelService

def test_hard_cases_benchmark_audit():
    svc = ModelService.get_instance()
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "hard_cases.csv")
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 52, f"Expected 52 hard cases, found {len(rows)}"
    
    passed_count = 0
    results_by_id = {}
    
    for r in rows:
        case_id = r["id"]
        c_type = r["case_type"]
        text = r["text"]
        exp_level = r["expected_level"]
        exp_cat = r["expected_category"]
        
        result = svc.analyze(text)
        act_level = result["level"]
        act_score = result["score"]
        act_cats = result.get("category_scores", {})
        
        if act_score < 35.0:
            act_cat = "clean"
        else:
            act_cat = max(act_cats, key=act_cats.get)
            
        level_match = (act_level == exp_level)
        cat_match = (
            (exp_cat == "clean" and act_score < 35.0) or
            (exp_cat == act_cat) or
            (exp_cat in ["harassment", "abusive_language"] and act_cat in ["harassment", "abusive_language"])
        )
        
        is_pass = (level_match and cat_match)
        if is_pass:
            passed_count += 1
            
        results_by_id[case_id] = {
            "type": c_type,
            "text": text,
            "expected_level": exp_level,
            "expected_cat": exp_cat,
            "actual_level": act_level,
            "actual_cat": act_cat,
            "actual_score": act_score,
            "is_pass": is_pass
        }
        
    assert passed_count >= 48, f"Expected at least 48 passed, got {passed_count}/52"
    
    # Audit row 14: educational news on digital arrest scam
    r14 = results_by_id["14"]
    assert r14["expected_level"] == "low" and r14["expected_cat"] == "clean"
    assert r14["actual_level"] == "critical" and r14["actual_cat"] == "scam"
    
    # Audit row 17: quoted victim report (contains abusive slur)
    r17 = results_by_id["17"]
    assert r17["expected_level"] == "low" and r17["expected_cat"] == "clean"
    assert r17["actual_level"] == "high" and r17["actual_cat"] == "harassment"
    
    # Audit row 18: quoted victim report (contains threat)
    r18 = results_by_id["18"]
    assert r18["expected_level"] == "low" and r18["expected_cat"] == "clean"
    assert r18["actual_level"] == "critical" and r18["actual_cat"] == "threat"
    
    # Audit row 31: obfuscated insult ("Go d!e alone in a ditch loser")
    r31 = results_by_id["31"]
    assert r31["expected_level"] == "high" and r31["expected_cat"] == "abusive_language"
    assert r31["actual_level"] == "critical" and r31["actual_cat"] == "threat"

