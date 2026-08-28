import json
from app import app
from services.prediction_service import PredictionService
from services.guidance_service import GuidanceService

def run_diagnostics():
    text = "I know where you live. If you don't send me $5000 in Bitcoin by tomorrow, I will ruin your life and hurt your family."
    
    print("--- Running Pipeline ---")
    result = PredictionService.classify_text(text)
    result = PredictionService.attach_risk_and_similarity(result, text)
    
    primary_label = result.get("primary_label", "none")
    primary_confidence = result.get("confidence", 0.0)
    secondary_labels = result.get("secondary_labels", {})
    risk_score = result.get("risk_score", 0)
    
    print("--- Inputs to get_guidance() ---")
    print(f"primary_label: {repr(primary_label)}")
    print(f"primary_confidence: {repr(primary_confidence)}")
    print(f"secondary_labels: {repr(secondary_labels)}")
    print(f"risk_score: {repr(risk_score)}")
    
    guidance_data = GuidanceService.get_guidance(
        primary_label, primary_confidence, secondary_labels, risk_score
    )
    
    print("--- Output from get_guidance() ---")
    print(json.dumps(guidance_data, indent=2))
    
    with open('backend/config/guidance_v1.json', 'r') as f:
        config = json.load(f)
    always_critical = config['severity_tiers']['always_critical']
    print("\n--- Byte-for-byte Comparison ---")
    print(f"primary_label in always_critical? {primary_label in always_critical}")
    for item in always_critical:
        if item.lower() == primary_label.lower():
            print(f"Found case-insensitive match: {repr(item)}")
            print(f"Lengths: {len(item)} vs {len(primary_label)}")

if __name__ == "__main__":
    with app.app_context():
        run_diagnostics()
