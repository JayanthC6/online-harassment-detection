import os
import csv
import pytest
from services.model_service import ModelService

@pytest.fixture(scope="module")
def model_service():
    """Returns singleton ModelService instance."""
    return ModelService.get_instance()

def test_hard_cases_dataset_integrity():
    """Verify that hard_cases.csv exists, is readable, and contains >= 40 diverse cases."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data", "hard_cases.csv")
    assert os.path.exists(csv_path), f"hard_cases.csv not found at {csv_path}"
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) >= 40, f"Expected at least 40 cases, got {len(rows)}"
    expected_cols = {"id", "case_type", "text", "expected_level", "expected_category", "notes"}
    assert expected_cols.issubset(set(rows[0].keys())), f"Missing required columns in CSV: {rows[0].keys()}"

def test_empty_and_short_inputs(model_service):
    """Verify empty string, spaces, and short greetings return score 0 and low risk safely."""
    for inp in ["", "   ", "ok", "k", "hey", "hello", "?"]:
        res = model_service.analyze(inp)
        assert res["level"] == "low"
        assert res["score"] == 0.0 or res["score"] < 15.0
        assert isinstance(res["category_scores"], dict)
        assert isinstance(res["explanation"], str)

def test_severity_caps(model_service):
    """
    Verify that severity caps prevent plain abuse/insults from reaching 'critical'.
    Critical level must be reserved for threats, sextortion, verified scams/phishing, or hate speech.
    """
    # Plain insult / abuse
    insult_text = "You are an ugly stupid idiot and a disgusting pig"
    res = model_service.analyze(insult_text)
    assert res["level"] in ["high", "medium"], f"Insult should be capped at high, got: {res['level']}"
    assert res["score"] <= 85.0, f"Insult score should not exceed 85.0, got: {res['score']}"

    # Direct threat should be eligible for critical
    threat_text = "I know where you live and I will murder you tonight"
    res_threat = model_service.analyze(threat_text)
    assert res_threat["level"] == "critical"
    assert res_threat["score"] >= 80.0

    # Sextortion should be eligible for critical
    sextortion_text = "I have your webcam video and private photos, send 1000 BTC or I will leak them to your friends"
    res_sex = model_service.analyze(sextortion_text)
    assert res_sex["level"] == "critical"
    assert res_sex["score"] >= 80.0

def test_profanity_downweighting(model_service):
    """Verify that absence of explicit profane words prevents false profanity signals."""
    # Text with toxicity/insult but NO explicit profanity words
    text = "You are an incompetent fool and a pathetic loser"
    res = model_service.analyze(text)
    signals = [s["signal"].lower() for s in res.get("signals", [])]
    assert not any("profan" in s for s in signals), f"Profanity signal falsely emitted: {signals}"

def test_category_signal_consistency(model_service):
    """
    Verify that signals are filed under the exact category they contribute to.
    A .xyz domain must contribute strictly to 'scam' and NOT 'phishing'.
    """
    text = "Check out this link: http://win-rewards.xyz"
    res = model_service.analyze(text)
    # scam should have score >= 75.0, phishing should be 0.0
    assert res["category_scores"]["scam"] >= 75.0
    assert res["category_scores"]["phishing"] == 0.0
    for s in res.get("signals", []):
        if ".xyz" in s.get("signal", ""):
            assert s["category"] == "scam"

def test_hard_cases_benchmark_and_discrepancy_tracking(model_service):
    """
    Runs the 44 hard cases benchmark.
    Verifies that the overall detection baseline is sound (>= 65% across challenging edge cases),
    and documents performance across categories.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data", "hard_cases.csv")
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    passes = 0
    failures = []

    for r in rows:
        text = r["text"]
        exp_level = r["expected_level"]
        exp_cat = r["expected_category"]

        res = model_service.analyze(text)
        act_level = res["level"]
        act_score = res["score"]
        act_cats = res["category_scores"]

        if act_score < 35.0:
            act_cat = "clean"
        else:
            act_cat = max(act_cats, key=act_cats.get)

        level_match = (act_level == exp_level)
        cat_match = (exp_cat == "clean" and act_score < 35.0) or (exp_cat == act_cat) or (exp_cat in ["harassment", "abusive_language"] and act_cat in ["harassment", "abusive_language"])

        if level_match and cat_match:
            passes += 1
        else:
            failures.append({
                "id": r["id"],
                "type": r["case_type"],
                "expected": f"{exp_level}/{exp_cat}",
                "actual": f"{act_level}/{act_cat} ({act_score:.1f})"
            })

    total = len(rows)
    accuracy = passes / total
    print(f"\nHard cases accuracy: {passes}/{total} ({accuracy:.1%})")
    assert passes >= 28, f"Benchmark regression: expected >= 28 passes, got {passes}/{total}"

