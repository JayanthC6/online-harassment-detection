import os
import sys

# Reconfigure stdout for UTF-8 on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure backend is on sys.path
sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

from ml.chatbot import generate_chat_response
from services.model_service import ModelService

ms = ModelService.get_instance()

output_lines = []

def log(s=""):
    print(s)
    output_lines.append(s)

# 1. SBI SMS
sbi_text = (
    "Urgent: Your SBI net banking account has been temporarily locked due to suspicious activity. "
    "Verify KYC immediately at http://sbi-kyc-update.xyz or call +919876543210. "
    "Failure to update within 24 hours will lead to permanent account suspension."
)
sbi_analysis = ms.analyze(sbi_text)

log("=== SBI SMS ANALYST ===")
resp_sbi_analyst = generate_chat_response(
    history=[{"role": "user", "content": "Please analyze this SMS message"}],
    persona="analyst",
    prediction_context=sbi_analysis
)
log(str(resp_sbi_analyst))
log(f"\n[Engine: {getattr(resp_sbi_analyst, 'engine', 'unknown')}]")

# 2. Sextortion
sex_text = (
    "I recorded you through your webcam while you were watching adult videos. "
    "Send 50000 rupees to my Bitcoin wallet within 24 hours or I will send the video to all your Instagram followers and family contacts."
)
sex_analysis = ms.analyze(sex_text)

log("\n=== SEXTORTION ANALYST ===")
resp_sex_analyst = generate_chat_response(
    history=[{"role": "user", "content": "Evaluate this threat for me"}],
    persona="analyst",
    prediction_context=sex_analysis
)
log(str(resp_sex_analyst))
log(f"\n[Engine: {getattr(resp_sex_analyst, 'engine', 'unknown')}]")

log("\n=== SEXTORTION VICTIM ===")
resp_sex_victim = generate_chat_response(
    history=[{"role": "user", "content": "Someone sent me this message saying they will leak my videos if I do not pay 50000 rupees in 24 hours on Instagram. I am terrified, what should I do?"}],
    persona="victim",
    prediction_context=sex_analysis
)
log(str(resp_sex_victim))
log(f"\n[Engine: {getattr(resp_sex_victim, 'engine', 'unknown')}]")

with open("scripts/chatbot_outputs.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))
log("\nWrote output to scripts/chatbot_outputs.txt")
