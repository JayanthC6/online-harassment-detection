import sys
sys.path.append(r"c:\Users\jayanth\Downloads\online-harassment-detection\backend")
from dotenv import load_dotenv
load_dotenv(r"c:\Users\jayanth\Downloads\online-harassment-detection\backend\.env")
from ml.explain_transformer import compute_ig_attributions

texts = [
    "I will kill you",
    "You are a stupid idiot.",
    "This is a longer message that might have different batching behavior during captum execution. " * 10
]

for t in texts:
    try:
        print("Testing:", t[:30])
        compute_ig_attributions(t, "Threat")
        print("Success")
    except Exception as e:
        print("Failed:", str(e))
