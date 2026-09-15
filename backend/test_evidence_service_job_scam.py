"""
test_evidence_service_job_scam.py
----------------------------------
Tests for EvidenceService.get_action_plan() covering the
Job / Recruitment Intelligence integration fix.

TEST 1  – Suspicious recruitment → plan = "Potentially Suspicious Recruitment Incident"
TEST 2  – Legitimate recruitment  → existing safe behavior preserved
TEST 3  – Normal cyber threat     → existing threat behavior unchanged
TEST 4  – Missing job_scam_signals → no crash, existing behavior preserved
TEST 5  – risk_score not modified  → service never touches risk_score
"""
import pytest

from services.evidence_service import EvidenceService


# ─── helpers ────────────────────────────────────────────────────────────────

def _make_result(
    primary_label="Clean",
    severity_tier="Safe",
    risk_score=5.0,
    job_scam_signals=None,
    threat_intel=None,
):
    """Build a minimal prediction_result dict."""
    ti = threat_intel if threat_intel is not None else {}
    if job_scam_signals is not None:
        ti = dict(ti)
        ti["job_scam_signals"] = job_scam_signals
    return {
        "primary_label": primary_label,
        "severity_tier": severity_tier,
        "risk_score": risk_score,
        "platform": "generic",
        "pii_categories": [],
        "threat_intel": ti,
    }


def _suspicious_job_scam_signals(extra_indicators=None):
    indicators = ["payment_before_joining", "suspicious_communication"]
    if extra_indicators:
        indicators += extra_indicators
    return {
        "detected": True,
        "recruitment_context": True,
        "detected_suspicious": True,
        "indicators": indicators,
        "assessment": "Potentially Suspicious Recruitment Document",
        "confidence": 0.85,
    }


def _legitimate_job_scam_signals():
    return {
        "detected": True,
        "recruitment_context": True,
        "detected_suspicious": False,
        "indicators": [],
        "assessment": "Legitimate recruitment context",
        "confidence": 0.4,
    }


# ─── Force reload of playbooks between tests ────────────────────────────────

@pytest.fixture(autouse=True)
def reset_playbooks():
    """Clear the cached playbooks so JSON changes are picked up."""
    EvidenceService._playbooks = None
    yield
    EvidenceService._playbooks = None


# ─── TEST 1: Suspicious recruitment ─────────────────────────────────────────

class TestSuspiciousRecruitment:
    """
    Input like: "Please pay ₹4,999 as a refundable registration fee before joining."
    The ML model gives risk_score=5, severity_tier=Safe, primary_label=Clean.
    But job_scam_signals.detected_suspicious = True.
    """

    def _plan(self, indicators=None):
        result = _make_result(
            primary_label="Clean",
            severity_tier="Safe",
            risk_score=5.0,
            job_scam_signals=_suspicious_job_scam_signals(extra_indicators=indicators),
        )
        return EvidenceService.get_action_plan(result), result

    def test_case_summary_is_recruitment_specific(self):
        plan, _ = self._plan()
        assert plan["case_summary"] == "Potentially Suspicious Recruitment Incident"

    def test_why_flagged_is_recruitment_specific(self):
        plan, _ = self._plan()
        assert "Safe Risk Incident" not in plan["why_flagged"]
        assert "Clean" not in plan["why_flagged"]
        assert "fraudulent or suspicious job offer" in plan["why_flagged"]

    def test_no_safe_risk_incident_in_summary(self):
        plan, _ = self._plan()
        assert "Safe Risk Incident" not in plan["case_summary"]
        assert "Clean" not in plan["case_summary"]

    def test_payment_safety_action_present(self):
        plan, _ = self._plan()
        joined = " ".join(plan["safety_actions"]).lower()
        assert "payment" in joined

    def test_employer_verification_action_present(self):
        plan, _ = self._plan()
        joined = " ".join(plan["safety_actions"]).lower()
        assert "verify" in joined or "employer" in joined

    def test_no_immediate_safety_actions_required_string(self):
        plan, _ = self._plan()
        for action in plan["safety_actions"]:
            assert "no immediate safety actions required" not in action.lower()
        # There must be at least one action
        assert len(plan["safety_actions"]) > 0

    def test_recommended_steps_present(self):
        plan, _ = self._plan()
        assert len(plan["recommended_steps"]) > 0

    def test_indicator_bullets_prepended(self):
        """Detected indicators should appear in safety_actions."""
        plan, _ = self._plan()
        joined = " ".join(plan["safety_actions"]).lower()
        assert "payment" in joined  # payment_before_joining → "Payment demanded..."

    def test_risk_score_not_modified(self):
        """EvidenceService must NEVER write to risk_score."""
        result = _make_result(
            primary_label="Clean",
            severity_tier="Safe",
            risk_score=5.0,
            job_scam_signals=_suspicious_job_scam_signals(),
        )
        original_risk = result["risk_score"]
        EvidenceService.get_action_plan(result)
        assert result["risk_score"] == original_risk, (
            "risk_score must not be modified by EvidenceService"
        )


# ─── TEST 2: Legitimate recruitment ─────────────────────────────────────────

class TestLegitimateRecruitment:
    """
    Input: "Our company follows a strict zero-fee recruitment policy..."
    recruitment_context=True, detected_suspicious=False → normal safe behavior.
    """

    def _plan(self):
        result = _make_result(
            primary_label="Clean",
            severity_tier="Safe",
            risk_score=5.0,
            job_scam_signals=_legitimate_job_scam_signals(),
        )
        return EvidenceService.get_action_plan(result)

    def test_no_suspicious_recruitment_case_summary(self):
        plan = self._plan()
        assert "Potentially Suspicious Recruitment Incident" not in plan["case_summary"]

    def test_safe_behavior_preserved(self):
        plan = self._plan()
        # Normal safe plan clears safety_actions to empty
        assert plan["safety_actions"] == []

    def test_recommended_steps_is_normal_safe(self):
        plan = self._plan()
        assert any("No specific action required" in s for s in plan["recommended_steps"])


# ─── TEST 3: Normal cyber threat (threat label, high severity) ───────────────

class TestNormalCyberThreat:
    """
    Existing threat behavior must be completely unchanged when no recruitment
    signals are present.
    """

    def _plan(self):
        result = _make_result(
            primary_label="Threat",
            severity_tier="High",
            risk_score=95.0,
            job_scam_signals=None,
        )
        return EvidenceService.get_action_plan(result)

    def test_case_summary_is_threat(self):
        plan = self._plan()
        assert "Threat" in plan["case_summary"]
        assert "Potentially Suspicious Recruitment" not in plan["case_summary"]

    def test_has_safety_actions(self):
        plan = self._plan()
        assert len(plan["safety_actions"]) > 0

    def test_no_recruitment_wording(self):
        plan = self._plan()
        joined = " ".join(plan["safety_actions"] + plan["recommended_steps"]).lower()
        assert "job offer" not in joined
        assert "recruitment" not in joined


# ─── TEST 4: Missing / null job_scam_signals ─────────────────────────────────

class TestMissingJobScamSignals:
    """
    When job_scam_signals is absent or null, existing behavior is preserved
    and there is no crash.
    """

    def test_none_threat_intel(self):
        result = {
            "primary_label": "Clean",
            "severity_tier": "Safe",
            "risk_score": 5.0,
            "platform": "generic",
            "pii_categories": [],
            "threat_intel": None,
        }
        plan = EvidenceService.get_action_plan(result)
        # Should not crash; should return normal safe plan
        assert "case_summary" in plan
        assert "Potentially Suspicious Recruitment" not in plan["case_summary"]

    def test_missing_threat_intel_key(self):
        result = {
            "primary_label": "Clean",
            "severity_tier": "Safe",
            "risk_score": 5.0,
            "platform": "generic",
            "pii_categories": [],
            # 'threat_intel' key absent entirely
        }
        plan = EvidenceService.get_action_plan(result)
        assert "case_summary" in plan
        assert "Potentially Suspicious Recruitment" not in plan["case_summary"]

    def test_job_scam_signals_key_missing_from_threat_intel(self):
        result = _make_result(
            primary_label="Clean",
            severity_tier="Safe",
            risk_score=5.0,
            threat_intel={"threat_signals": {}},  # no job_scam_signals key
        )
        plan = EvidenceService.get_action_plan(result)
        assert "case_summary" in plan
        assert "Potentially Suspicious Recruitment" not in plan["case_summary"]

    def test_detected_suspicious_false(self):
        result = _make_result(
            primary_label="Clean",
            severity_tier="Safe",
            risk_score=5.0,
            job_scam_signals={"detected": False, "detected_suspicious": False,
                               "recruitment_context": False, "indicators": []},
        )
        plan = EvidenceService.get_action_plan(result)
        assert "Potentially Suspicious Recruitment" not in plan["case_summary"]


# ─── TEST 5: Risk score preservation ─────────────────────────────────────────

class TestRiskScorePreservation:
    """EvidenceService.get_action_plan() must NEVER write back to risk_score."""

    @pytest.mark.parametrize("risk_score,detected_suspicious", [
        (5.0,  True),
        (5.0,  False),
        (95.0, False),
        (0.0,  True),
    ])
    def test_risk_score_unchanged(self, risk_score, detected_suspicious):
        jss = {
            "detected": True,
            "recruitment_context": True,
            "detected_suspicious": detected_suspicious,
            "indicators": ["payment_before_joining"] if detected_suspicious else [],
        }
        result = _make_result(
            primary_label="Clean",
            severity_tier="Safe" if risk_score < 50 else "High",
            risk_score=risk_score,
            job_scam_signals=jss,
        )
        EvidenceService.get_action_plan(result)
        assert result["risk_score"] == risk_score, (
            f"risk_score was mutated: expected {risk_score}, got {result['risk_score']}"
        )
