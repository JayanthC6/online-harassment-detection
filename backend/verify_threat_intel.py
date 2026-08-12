import os
import sys
import torch
from dotenv import load_dotenv

# Ensure we can import from backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from ml.adapters.heuristic import PrimaryModelAdapter, HeuristicMultiLabelAdapter

def run_tests():
    print("Initializing Neurosymbolic Fusion Pipeline with Threat Intel...")
    primary = PrimaryModelAdapter()
    engine = HeuristicMultiLabelAdapter(primary)
    
    print("\n--- BASELINE TEST: Regex Only ---")
    text_base = "Verify your account here: http://example.com"
    print(f"Text: '{text_base}'")
    res_base = engine.predict(text_base)
    print(f"Threat Intel: {res_base.get('threat_intel')}")
    print(f"Debug Base Symbolic Confs: {res_base.get('debug_base_s')}")
    print(f"Debug TI Confs: {res_base.get('debug_ti_confs')}")
    print(f"Debug Final Symbolic Confs: {res_base.get('debug_symbolic_confs')}")
    print(f"Primary Label: {res_base.get('primary_label')} ({res_base.get('confidence')})")

    # 1. Safe Browsing Isolation
    print("\n--- TEST CASE 1: Safe Browsing Isolation ---")
    text1 = "Look at this cool site http://malware.testing.google.test/testing/malware/"
    print(f"Text: '{text1}'")
    res1 = engine.predict(text1)
    
    print(f"Threat Intel: {res1.get('threat_intel')}")
    print(f"Debug Base Symbolic Confs: {res1.get('debug_base_s')}")
    print(f"Debug TI Confs: {res1.get('debug_ti_confs')}")
    print(f"Debug Final Symbolic Confs: {res1.get('debug_symbolic_confs')}")
    print(f"Primary Label: {res1.get('primary_label')} ({res1.get('confidence')})")
    
    # 2. Typosquat Isolation
    print("\n--- TEST CASE 2: Typosquat Isolation ---")
    text2 = "Check this out http://paypa1.com"
    print(f"Text: '{text2}'")
    res2 = engine.predict(text2)
    print(f"Threat Intel: {res2.get('threat_intel')}")
    print(f"Debug Base Symbolic Confs: {res2.get('debug_base_s')}")
    print(f"Debug TI Confs: {res2.get('debug_ti_confs')}")
    print(f"Debug Final Symbolic Confs: {res2.get('debug_symbolic_confs')}")
    print(f"Primary Label: {res2.get('primary_label')} ({res2.get('confidence')})")
    
    # 3. Combined
    print("\n--- TEST CASE 3: Combined Regex + Typosquat ---")
    text3 = "Verify your account here: http://paypa1.com"
    print(f"Text: '{text3}'")
    res3 = engine.predict(text3)
    print(f"Threat Intel: {res3.get('threat_intel')}")
    print(f"Debug Base Symbolic Confs: {res3.get('debug_base_s')}")
    print(f"Debug TI Confs: {res3.get('debug_ti_confs')}")
    print(f"Debug Final Symbolic Confs: {res3.get('debug_symbolic_confs')}")
    print(f"Primary Label: {res3.get('primary_label')} ({res3.get('confidence')})")
    
if __name__ == "__main__":
    run_tests()
