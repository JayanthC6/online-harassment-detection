import sys
import os
import json

# Ensure we can import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.prediction_service import PredictionService
import services.prediction_service as ps
from ml.adapters.heuristic import PrimaryModelAdapter

# Disable similarity lookup to prevent MongoDB timeout delays
ps._similarity_available = False

def main():
    test_cases = [
        # A. Safe
        {"text": "Hello! How are you doing today?", "expected": "Clean"},
        {"text": "Great job on the presentation, you nailed it.", "expected": "Clean"},
        {"text": "Could you please send me the report when you have time?", "expected": "Clean"},
        {"text": "I will be out of office tomorrow.", "expected": "Clean"},
        {"text": "What time is the meeting scheduled for?", "expected": "Clean"},
        {"text": "Looking forward to working with you on this project.", "expected": "Clean"},
        {"text": "Thank you for the quick response.", "expected": "Clean"},
        {"text": "Let's touch base next week.", "expected": "Clean"},

        # B. Harassment
        {"text": "You are worthless, just disappear already", "expected": "harassing"}, # The original failure case
        {"text": "You're an absolute idiot and everyone hates you.", "expected": "harassing"},
        {"text": "I hope you die.", "expected": "harassing"},
        {"text": "You are so ugly it's disgusting.", "expected": "harassing"},
        {"text": "Shut up you stupid bitch.", "expected": "harassing"},
        {"text": "You subhuman trash.", "expected": "harassing"},
        {"text": "Nobody likes you, kill yourself.", "expected": "harassing"},
        {"text": "I am going to beat you up after school.", "expected": "harassing"},

        # C. Digital Safety
        {"text": "Urgent action required: verify your account at http://fake-login.com", "expected": "harassing"},
        {"text": "Send 0.5 bitcoin to this address to get guaranteed returns.", "expected": "harassing"},
        {"text": "I am the real admin, pretending to be you.", "expected": "harassing"},
        {"text": "I have your photos. Pay me or I will leak them.", "expected": "harassing"},
        {"text": "Transfer funds immediately or else.", "expected": "harassing"},
        {"text": "Wire me the money to this fake bank account.", "expected": "harassing"},
        {"text": "What is your mother's maiden name?", "expected": "harassing"},
        {"text": "Send me a code so I can reset my password.", "expected": "harassing"},

        # D. Mixed Attacks
        {"text": "Listen you worthless idiot, I have your photos. Pay me or I will leak them.", "expected": "harassing"},
        {"text": "Verify your account at this link or I will destroy you.", "expected": "harassing"},
        {"text": "I'm the real CEO, you dumb trash. Transfer funds immediately.", "expected": "harassing"},
        {"text": "Can you do me a quick favor and buy a gift card you stupid bitch.", "expected": "harassing"},
        {"text": "Send bitcoin to this address, nobody likes you anyway.", "expected": "harassing"},
        {"text": "You're a nazi scum, pay me or I expose you.", "expected": "harassing"}
    ]

    results = []
    primary = PrimaryModelAdapter()

    print("Running Prediction Validation Suite...\n")

    md_content = "# Validation Report\n\n"

    for idx, tc in enumerate(test_cases, 1):
        text = tc["text"]
        expected = tc["expected"]
        
        # We also want to log what the pure DistilBERT output was
        base_result = primary.predict(text)
        distilbert_label = base_result["primary_label"]
        distilbert_conf = base_result["confidence"]

        # Run the full pipeline
        result = PredictionService.classify_text(text)
        result = PredictionService.attach_risk_and_similarity(result, text)

        actual_primary = result["primary_label"]
        actual_label = result["label"]
        secondary = list(result.get("secondary_labels", {}).keys())
        conf = result["confidence"]
        risk = result.get("risk_score", 0)

        # Pass logic
        if expected == "Clean":
            passed = actual_primary == "Clean" and actual_label == "non_harassing"
        else:
            passed = actual_primary != "Clean" and actual_label == "harassing"

        # Explicit failure case check:
        if "worthless" in text and "disappear" in text:
            if actual_label != "harassing":
                passed = False

        status = "PASS" if passed else "FAIL"

        md_content += f"### Test {idx}: {'✅ PASS' if passed else '❌ FAIL'}\n"
        md_content += f"- **Input:** `{text}`\n"
        md_content += f"- **Expected:** `{expected}`\n"
        md_content += f"- **DistilBERT Base:** `{distilbert_label}` (conf: {distilbert_conf:.4f})\n"
        md_content += f"- **Final Primary:** `{actual_primary}`\n"
        md_content += f"- **Secondary:** `{secondary}`\n"
        md_content += f"- **Confidence:** `{conf:.4f}`\n"
        md_content += f"- **Risk Score:** `{risk}`\n\n"

        print(f"[{status}] Test {idx}")

    # Output JSON for the agent to parse
    with open("C:/Users/jayanth/.gemini/antigravity-ide/brain/0d57f3c6-97d5-449d-937b-ac05c5550756/validation_report.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print("\nValidation complete. Results saved to validation_report.md")

if __name__ == "__main__":
    main()

