import pytest
import json
from services.evidence_service import EvidenceService

def test_whatsapp_harassment():
    result = {
        "primary_label": "hate_speech",
        "severity_tier": "Medium",
        "platform": "whatsapp",
        "messages": [{"text": "You are terrible."}],
        "pii_categories": []
    }
    plan = EvidenceService.get_action_plan(result)
    
    assert plan["case_summary"] == "Medium Risk Incident - Hate Speech"
    assert "Detected 1 message involving hate speech" in plan["why_flagged"]
    assert any("WhatsApp" in item for item in plan["evidence_checklist"])
    assert any("Block the sender" in item for item in plan["safety_actions"])

def test_threatening_email():
    result = {
        "primary_label": "threat",
        "severity_tier": "High",
        "platform": "email",
        "pii_categories": []
    }
    plan = EvidenceService.get_action_plan(result)
    
    assert plan["case_summary"] == "High Risk Incident - Threat"
    assert "Detected 1 message involving threat" in plan["why_flagged"]
    assert any("Explicit threat content" in item for item in plan["evidence_checklist"])
    assert any("Ensure your physical safety" in item for item in plan["safety_actions"])
    assert any("Contact local law enforcement" in item for item in plan["recommended_steps"])

def test_extortion():
    # Extortion falls under threat or scam in our current simplified playbook
    # We will map extortion to threat for testing
    result = {
        "primary_label": "scam",
        "severity_tier": "Critical",
        "platform": "generic",
        "pii_categories": ["email_address", "bank_account"]
    }
    plan = EvidenceService.get_action_plan(result)
    
    assert plan["case_summary"] == "Critical Risk Incident - Scam"
    assert any("Requested payment methods" in item for item in plan["evidence_checklist"])
    assert any("Do not send money" in item for item in plan["safety_actions"])
    assert any("financial institutions" in item for item in plan["safety_actions"]) # from pii_exposed

def test_phishing_email():
    result = {
        "primary_label": "phishing",
        "severity_tier": "High",
        "platform": "email",
        "pii_categories": []
    }
    plan = EvidenceService.get_action_plan(result)
    
    assert plan["case_summary"] == "High Risk Incident - Phishing"
    assert any("Malicious URLs" in item for item in plan["evidence_checklist"])
    assert any("Do not enter any credentials" in item for item in plan["safety_actions"])
    assert any("Two-Factor Authentication" in item for item in plan["safety_actions"])

def test_threatening_document():
    result = {
        "primary_label": "threat",
        "severity_tier": "Critical",
        "platform": "generic",
        "pii_categories": []
    }
    plan = EvidenceService.get_action_plan(result)
    
    assert plan["case_summary"] == "Critical Risk Incident - Threat"
    assert any("Explicit threat content" in item for item in plan["evidence_checklist"])

def test_pii_non_leakage():
    # Inject a known fake PII string
    sensitive_pii = "JANE_DOE_SSN_123456789"
    result = {
        "primary_label": "hate_speech",
        "severity_tier": "Low",
        "platform": "whatsapp",
        "messages": [{"text": f"Hey {sensitive_pii}, I hate you."}],
        "pii_categories": ["SSN"],
        "text": f"Hey {sensitive_pii}, I hate you." # in case it's parsed directly
    }
    plan = EvidenceService.get_action_plan(result)
    
    # Assert that the PII string does NOT appear anywhere in the output JSON values
    plan_json = json.dumps(plan)
    assert sensitive_pii not in plan_json, "PII leak detected in evidence plan!"
