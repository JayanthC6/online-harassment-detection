import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

# Temporarily point SHIELDAI_MODEL_DIR to non-existent directory
os.environ["SHIELDAI_MODEL_DIR"] = "backend/models/non_existent_dir"

from services.model_service import ModelService

print("Testing fallback initialization when model files are missing...")
service = ModelService()

assert not service.is_loaded, "Model should not be loaded when directory is missing"
assert service.model is None, "Model should be None"

# Run prediction
res = service.analyze("Dear user, your SBI account is suspended. Verify at https://bit.ly/sbi-kyc")
print("Fallback prediction result:")
print(f"Score: {res['score']}, Level: {res['level']}, Category: {res['category_scores']}, Layer: {res['which_layer']}")
assert res["score"] > 50, "Rules should still trigger on phishing even without the model"
assert res["which_layer"] == "rules", "Layer should be 'rules'"
print("[PASS] Fallback mode verified: App starts and functions cleanly with rules when model files are missing!")

