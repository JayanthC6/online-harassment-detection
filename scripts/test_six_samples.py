import sys
import os

try:
    import torch
except Exception:
    pass

import json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))
from services.prediction_service import PredictionService

inputs = [
    ("1. SBI Phishing SMS with short link", "Urgent: Your SBI net banking account has been temporarily blocked due to pending KYC. Click http://bit.ly/sbi-kyc-update to verify your details immediately."),
    ("2. Lottery Scam", "Congratulations! You have won $1,000,000 in the International Postcode Lottery. Claim your prize by sending your bank details to claim@postcode-lottery.xyz"),
    ("3. Direct Threat", "I know where you live and I will murder you tonight. Watch your back."),
    ("4. Sextortion Message", "I have recorded a video of you through your webcam doing private things. Send $500 in Bitcoin to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa or I will send it to all your contacts and family."),
    ("5. Abusive Insult", "You are an absolute piece of trash and the most disgusting idiot I have ever seen."),
    ("6. Harmless Message", "Hey, are we still meeting for lunch tomorrow at 1 PM?")
]

for title, text in inputs:
    res = PredictionService.classify_text(text)
    print(f"=== {title} ===")
    print(f"Input: {text}")
    print(f"Score: {res['score']} | Level: {res['level']} | Severity Tier: {res.get('severity_tier')} | Primary: {res.get('primary_label')}")
    print(f"Categories: {res.get('category_scores')}")
    signals = [s.get('signal', s) if isinstance(s, dict) else str(s) for s in res.get('signals', [])]
    print(f"Signals: {signals}")
    print()
