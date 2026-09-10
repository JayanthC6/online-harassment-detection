import sys
sys.path.append(r"c:\Users\jayanth\Downloads\online-harassment-detection\backend")
from dotenv import load_dotenv
load_dotenv(r"c:\Users\jayanth\Downloads\online-harassment-detection\backend\.env")
from ml.explain_transformer import compute_ig_attributions

tests = [
    {"text": "Have a wonderful day!", "label": "Threat"},
    {"text": "I am going to kill you, you stupid idiot.", "label": "Threat"},
    {"text": "This is a much longer sentence that we are using to verify whether the Integrated Gradients implementation can successfully handle multiple internal batches of input embeddings without throwing a shape mismatch tensor error like the old LIG implementation did.", "label": "Threat"}
]

for t in tests:
    print(f"Testing length {len(t['text'].split())} words...")
    try:
        res = compute_ig_attributions(t['text'], t['label'])
        tokens = res.get('tokens', [])
        print(f"Success! Method: {res.get('method')}, Tokens returned: {len(tokens)}")
        # Check alignment
        print("Sample token:", tokens[0] if tokens else None)
    except Exception as e:
        import traceback
        traceback.print_exc()
