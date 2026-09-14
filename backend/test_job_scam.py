import pytest
from ml.adapters.threat_intel import analyze_text_for_threat_intel, extract_pii, mask_pii
from services.prediction_service import PredictionService

# Mock for PredictionService to just return threat intel wrapper for explainability test
def get_mock_result(text):
    intel = analyze_text_for_threat_intel(text)
    
    result = {
        "text": text,
        "category": "none",
        "primary_label": "none",
        "confidence": 0.05,
        "secondary_labels": {},
        "risk_score": 0,
        "threat_intel": intel,
        "malicious_urls": intel.get("malicious_urls", [])
    }
    
    result = PredictionService.attach_risk_and_similarity(result, text)
    return result

def test_legitimate_job_document():
    text = "Congratulations! You have been selected for the position of Software Engineer. Your joining date is next week. Your salary is $100,000."
    intel = analyze_text_for_threat_intel(text)
    assert intel["job_scam_signals"]["detected"] == True
    assert intel["job_scam_signals"]["recruitment_context"] == True
    assert intel["job_scam_signals"]["detected_suspicious"] == False

def test_suspicious_job_document_payment():
    text = "You have been selected for the position. Please pay a processing fee of $50 before joining."
    intel = analyze_text_for_threat_intel(text)
    assert intel["job_scam_signals"]["detected"] == True
    assert intel["job_scam_signals"]["recruitment_context"] == True
    assert intel["job_scam_signals"]["detected_suspicious"] == True
    assert "payment_before_joining" in intel["job_scam_signals"]["indicators"]

def test_suspicious_contact():
    text = "We have a job offer for you. Please contact our HR only on whatsapp."
    intel = analyze_text_for_threat_intel(text)
    assert intel["job_scam_signals"]["detected_suspicious"] == True
    assert "suspicious_communication" in intel["job_scam_signals"]["indicators"]

def test_unusual_payment_method():
    text = "Your appointment is confirmed. Send the training fee via bitcoin."
    intel = analyze_text_for_threat_intel(text)
    assert intel["job_scam_signals"]["detected_suspicious"] == True
    assert "unusual_payment_method" in intel["job_scam_signals"]["indicators"]

def test_no_false_positive_on_negation():
    # The negative lookbehind/regex approach doesn't use lookbehinds currently (since we changed it to a simpler regex that matches "pay a processing fee" rather than just "processing fee")
    # Let's ensure it doesn't flag "We will never ask for a processing fee."
    text = "Congratulations on your new job. Please note we will never ask candidates for a processing fee or security deposit."
    intel = analyze_text_for_threat_intel(text)
    assert intel["job_scam_signals"]["recruitment_context"] == True
    # Should not flag payment_before_joining because the regex looks for "pay|deposit|transfer|send ... processing fee"
    assert "payment_before_joining" not in intel["job_scam_signals"]["indicators"]
    assert intel["job_scam_signals"]["detected_suspicious"] == False

def test_non_job_document():
    text = "Hey, can you pick up some groceries on the way home? Don't forget the milk."
    intel = analyze_text_for_threat_intel(text)
    assert intel["job_scam_signals"]["recruitment_context"] == False
    assert intel["job_scam_signals"]["detected_suspicious"] == False

def test_pii_handling_in_explainability():
    # Verify no raw PII ends up in the explainability reasons
    text = "Job offer for John Doe (Phone: +91-9876543210). Please pay a registration fee."
    result = get_mock_result(text)
    
    reasons = result["flagging_reasons"]
    reasons_text = " ".join(reasons)
    
    assert "+91-9876543210" not in reasons_text
    assert "payment-related recruitment indicator" in reasons_text
    
def test_suspicious_url():
    # Mocking Safe Browsing is hard without monkeypatching, so we'll test IP-based or Shortener which are deterministic locally
    text = "Job offer. Please review http://192.168.1.5/login"
    intel = analyze_text_for_threat_intel(text)
    
    # URL is flagged as IP-based
    assert any(u["url"] == "http://192.168.1.5/login" for u in intel["threat_signals"]["ip_based_urls"])
    
def test_shortened_url_job_scam():
    text = "You are selected for the position. See details http://bit.ly/12345"
    intel = analyze_text_for_threat_intel(text)
    
    assert any(u["url"] == "http://bit.ly/12345" for u in intel["threat_signals"]["url_shorteners"])
    assert intel["job_scam_signals"]["recruitment_context"] == True

def test_typosquatted_url_job_scam():
    text = "We have a job offer for you. Please accept it at http://paypa1.com/careers"
    intel = analyze_text_for_threat_intel(text)
    
    assert intel["job_scam_signals"]["recruitment_context"] == True
    assert intel["job_scam_signals"]["detected_suspicious"] == True
    assert "suspicious_url" in intel["job_scam_signals"]["indicators"]
    
    # Verify the typosquatting logic correctly flagged paypa1.com
    assert any(m["status"] == "High Risk" and "Typosquatting" in m["reason"] for m in intel["malicious_urls"])

