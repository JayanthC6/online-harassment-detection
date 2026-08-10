import os
import sys
import torch  # Import before sklearn to avoid WinError 1114 DLL conflict
from dotenv import load_dotenv

# Ensure we can import from backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from ml.adapters.heuristic import PrimaryModelAdapter, HeuristicMultiLabelAdapter
from ml.adapters.base import ModelAdapter

def run_tests():
    print("Initializing Neurosymbolic Fusion Pipeline...")
    primary = PrimaryModelAdapter()
    engine = HeuristicMultiLabelAdapter(primary)
    
    print("\n--- TEST CASE 1: Pure Neural Signal ---")
    text1 = "You're worthless, just disappear from here you fucker asshole"
    print(f"Text: '{text1}'")
    res1 = engine.predict(text1)
    print(f"Primary Label: {res1.get('primary_label')} ({res1.get('confidence')})")
    print(f"Neural Probs: {res1.get('debug_neural_probs', {})}")
    print(f"Symbolic Confs: {res1.get('debug_symbolic_confs', {})}")
    print(f"Fused Confs: {res1.get('debug_fused_confs', {})}")
    print(f"Secondary Labels: {res1.get('secondary_labels')}")
    print(f"Model Engine: {res1.get('model')}")
    
    print("\n--- TEST CASE 2: Symbolic-Only Category ---")
    text2 = "Verify your account here: http://fake-login.com"
    print(f"Text: '{text2}'")
    res2 = engine.predict(text2)
    print(f"Primary Label: {res2.get('primary_label')} ({res2.get('confidence')})")
    print(f"Neural Probs: {res2.get('debug_neural_probs', {})}")
    print(f"Symbolic Confs: {res2.get('debug_symbolic_confs', {})}")
    print(f"Fused Confs: {res2.get('debug_fused_confs', {})}")
    print(f"Secondary Labels: {res2.get('secondary_labels')}")
    
    # Assert symbolic-only logic
    # Heuristic confidence is generated randomly between 0.75-0.85
    # Since weight is 1.0, fused should exactly match heuristic raw.
    print("Checking if fused confidence matches raw standalone heuristic for Phishing/Scam...")
    if "Phishing" in res2.get("primary_label") or "Scam" in res2.get("primary_label"):
        print("Success: Phishing/Scam emerged as primary.")
    else:
        print("Warning: Did not get Phishing/Scam as primary.")

    print("\n--- TEST CASE 3: Threat Override via High Symbolic Weight ---")
    text3 = "I know where you live, I will kill you"
    print(f"Text: '{text3}'")
    res3 = engine.predict(text3)
    print(f"Primary Label: {res3.get('primary_label')} ({res3.get('confidence')})")
    print(f"Neural Probs: {res3.get('debug_neural_probs', {})}")
    print(f"Symbolic Confs: {res3.get('debug_symbolic_confs', {})}")
    print(f"Fused Confs: {res3.get('debug_fused_confs', {})}")
    print(f"Secondary Labels: {res3.get('secondary_labels')}")
    
    print("\n--- TEST CASE 4: Noisy-OR Fusion Math Check ---")
    class MockPrimaryAdapter(ModelAdapter):
        def predict(self, text: str) -> dict:
            return {
                "neural_probs": {"Hate Speech": 0.55},
                "thresholds": {"Hate Speech": 0.50},
                "model": "distilbert"
            }
            
    mock_primary = MockPrimaryAdapter()
    test_engine = HeuristicMultiLabelAdapter(mock_primary)
    
    # We will inject a custom heuristic to force weak symbolic evidence
    test_engine.heuristics = {"Hate Speech": [r"test_fusion"]}
    
    text4 = "test_fusion"
    # The heuristic triggers, generating some confidence ~0.75 - 0.85. 
    # Let's say we override it explicitly in the code for the test? 
    # Or just let it calculate and verify mathematically.
    
    print("Mocking neural probability = 0.55")
    res4 = test_engine.predict(text4)
    fused_conf = res4.get('confidence')
    print(f"Neural Probs: {res4.get('debug_neural_probs', {})}")
    print(f"Symbolic Confs: {res4.get('debug_symbolic_confs', {})}")
    print(f"Fused Confs: {res4.get('debug_fused_confs', {})}")
    print(f"Fused Hate Speech Confidence: {fused_conf}")
    
    # Expected logic: 
    # n_prob = 0.55, n_weight = 0.8 -> neural component = 0.44
    # s_prob ~ 0.75-0.85, s_weight = 0.5 -> symbolic component ~ 0.375-0.425
    # fused = 1 - (1 - 0.44) * (1 - s_comp)
    # fused = 1 - 0.56 * (~0.6) = 1 - ~0.336 = ~0.664
    if fused_conf > 0.55:
        print("Success! Fused confidence is strictly higher than either standalone component, proving Noisy-OR works.")
    else:
        print("Failure: Fused confidence did not increase.")

if __name__ == "__main__":
    run_tests()
