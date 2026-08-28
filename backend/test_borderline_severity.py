import json
from unittest.mock import patch
from app import app

def test_borderline():
    client = app.test_client()
    
    test_text = "This is a borderline test string."
    
    # Mock attach_risk_and_similarity to return a fixed risk_score of 70
    with patch('services.prediction_service.PredictionService.attach_risk_and_similarity') as mock_risk:
        mock_risk.return_value = {
            "primary_label": "Toxicity / Offensive Language",
            "confidence": 0.8,
            "secondary_labels": {},
            "risk_score": 70.0,
            "similarity_flag": False
        }
        
        # Test 1: Hit /complaints with the same mocked risk score
        print("--- Testing /complaints endpoint ---")
        # Generate a fake token or just bypass auth for the test if possible, 
        # or we can test the `summarize_complaint` function directly since it's the core logic.
        # It's easier to call `summarize_complaint` directly to avoid auth hurdles on /complaints.
        from ml.summarize import summarize_complaint
        
        complaint_res = summarize_complaint(test_text, "Toxicity / Offensive Language", 0.8, 70.0, "user")
        print(f"Severity from summarize_complaint (/complaints): {complaint_res.get('severity')}")
        
        
        # Test 2: Hit /demo/analyze endpoint 
        # Wait, /demo/analyze doesn't need auth.
        # But it requires example_id. We'll just patch DEMO_EXAMPLES in routes_public to accept "test"
        with patch.dict('api.routes_public.DEMO_EXAMPLES', {"test": test_text}):
            print("\n--- Testing /demo/analyze endpoint ---")
            demo_resp = client.post('/demo/analyze', json={"example_id": "test"})
            demo_data = json.loads(demo_resp.get_data(as_text=True))
            print(f"Severity from /demo/analyze: {demo_data.get('severity')}")

if __name__ == "__main__":
    test_borderline()
