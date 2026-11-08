import sys
import os
import json

sys.path.insert(0, os.path.abspath("backend"))

from services.model_service import model_service

test_cases = [
    {
        "id": "1_bank_sms_shortened_link",
        "description": "Fake Bank SMS with Shortened Link",
        "text": "Dear SBI customer, your account 5821 is suspended due to pending KYC update. Click immediately within 24 hours to verify: https://bit.ly/sbi-kyc-update"
    },
    {
        "id": "2_lottery_scam",
        "description": "Lottery Scam",
        "text": "CONGRATULATIONS! You have won $1,000,000 in the International Mobile Lucky Draw. To claim your cash prize, pay a $150 processing fee via Steam Gift Card or Bitcoin to prize@lottery-winner.xyz"
    },
    {
        "id": "3_direct_threat",
        "description": "Direct Threat",
        "text": "I know where you live and which gym you go to. I am going to find you tomorrow and kill you with my bare hands."
    },
    {
        "id": "4_sextortion_message",
        "description": "Sextortion Message",
        "text": "I recorded an intimate video from your webcam while you were visiting private sites. Pay me 0.5 BTC within 24 hours or I will leak these photos and video to all your friends and family."
    },
    {
        "id": "5_abusive_insult",
        "description": "Abusive Insult",
        "text": "You are a completely worthless, stupid idiot and a disgusting piece of trash. Nobody will ever care about you."
    },
    {
        "id": "6_harmless_message",
        "description": "Harmless Message",
        "text": "Hey Sarah, are we still meeting at the library at 4 PM to work on our computer science project?"
    }
]

print("=" * 80)
print("SHIELDAI PHASE 2 DETECTION ENGINE: 6 BENCHMARK INPUT TEST")
print("=" * 80)

outputs = []
for tc in test_cases:
    print(f"\n--- Testing: {tc['description']} ---")
    print(f"Input text: \"{tc['text']}\"")
    result = model_service.analyze(tc["text"])
    tc_output = {
        "test_case": tc["id"],
        "description": tc["description"],
        "input_text": tc["text"],
        "result": result
    }
    outputs.append(tc_output)
    print(json.dumps(result, indent=2))

# Save all results to artifact or json
with open("backend/data/phase2_test_results.json", "w", encoding="utf-8") as f:
    json.dump(outputs, f, indent=2)

print("\n" + "=" * 80)
print("All 6 test cases executed successfully!")
print("Saved full output to backend/data/phase2_test_results.json")
print("=" * 80)

