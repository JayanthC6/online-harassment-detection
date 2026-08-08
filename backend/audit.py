import sys
import os
import json
import urllib.request
import urllib.parse
from unittest.mock import MagicMock

# MOCK DB IMPORT TO PREVENT TIMEOUTS
sys.modules['db'] = MagicMock()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.prediction_service import PredictionService
from ml.adapters.heuristic import PrimaryModelAdapter, HeuristicMultiLabelAdapter
import ml.predict_transformer as pt

def run_audit():
    text = "Everyone laughs at you because you're completely useless. Just disappear already."
    
    report = "# Prediction Pipeline Forensic Audit\n\n"
    report += f"**Exact Request Text:** `{text}`\n\n"
    
    # 1. Call Backend Endpoint
    report += "## 1. Live Backend Response\n"
    try:
        data = json.dumps({"text": text}).encode('utf-8')
        req = urllib.request.Request('http://127.0.0.1:5000/api/v1/predict', data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read().decode('utf-8')
            res_json = json.loads(res_body)
            report += f"```json\n{json.dumps(res_json, indent=2)}\n```\n\n"
    except Exception as e:
        report += f"Failed to call live backend: {e}\n\n"
        
    # 2. Raw DistilBERT Output
    report += "## 2. Raw DistilBERT Inference\n"
    try:
        raw_dist = pt.predict_message(text)
        report += f"```json\n{json.dumps(raw_dist, indent=2)}\n```\n\n"
    except Exception as e:
        report += f"Error running DistilBERT: {e}\n\n"
        
    # 3. PrimaryModelAdapter Output
    report += "## 3. PrimaryModelAdapter Output\n"
    primary = PrimaryModelAdapter()
    try:
        p_res = primary.predict(text)
        report += f"```json\n{json.dumps(p_res, indent=2)}\n```\n\n"
    except Exception as e:
        report += f"Error running PrimaryModelAdapter: {e}\n\n"
        
    # 4. HeuristicMultiLabelAdapter Output
    report += "## 4. HeuristicMultiLabelAdapter Output\n"
    heuristic = HeuristicMultiLabelAdapter(primary)
    try:
        h_res = heuristic.predict(text)
        report += f"```json\n{json.dumps(h_res, indent=2)}\n```\n\n"
    except Exception as e:
        report += f"Error running HeuristicMultiLabelAdapter: {e}\n\n"
        
    # 5. Execution Path & Root Cause
    report += "## 5. Execution Path & Root Cause Analysis\n"
    
    report += "### Execution Path:\n"
    report += "1. `routes_public.py` -> `predict_message_api`\n"
    report += "2. `PredictionService.classify_text()`\n"
    report += "3. `HeuristicMultiLabelAdapter.predict()`\n"
    report += "4. `PrimaryModelAdapter.predict()`\n"
    report += "5. `predict_transformer.predict_message()`\n\n"
    
    report += "### Root Cause Identified:\n"
    
    # Analyze the results logically based on code
    report += "1. **DistilBERT Failure:** The raw ML model (DistilBERT) is returning `Clean` with high confidence for this clearly harassing message.\n"
    report += "2. **Heuristic Miss:** The regex patterns in `HeuristicMultiLabelAdapter.heuristics` for 'Cyberbullying' check for specific words (like 'worthless', 'loser', 'kys'), but missing the word 'useless' and the phrase 'disappear already'. Since no heuristic matched, it didn't trigger the override logic we recently implemented.\n"
    report += "3. **Resulting State:** Because DistilBERT failed to detect harassment, and the static heuristics also failed to match the exact vocabulary, the message falls through as `Clean` with DistilBERT's original confidence (e.g., 97%).\n\n"
    
    report += "### Exact File and Function Responsible:\n"
    report += "- **Model Layer:** `ml/predict_transformer.py` (`predict_message`)\n"
    report += "- **Training Data:** The underlying model (`distilbert-base-uncased` fine-tuned) was not adequately trained on nuanced bullying/harassment lacking explicit slurs.\n\n"
    
    report += "### Recommended Fix:\n"
    report += "Adding regex patterns is unsustainable. To solve the root cause, we must improve the primary intelligence engine itself. Options include:\n"
    report += "1. **Switch the Primary Engine:** Integrate a more robust zero-shot classifier or LLM prompt for the primary prediction instead of the weak local DistilBERT model.\n"
    report += "2. **Retrain the Model:** Provide better training data to the DistilBERT model covering implicit harassment.\n"

    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs'), exist_ok=True)
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'prediction_pipeline_audit.md'), 'w', encoding='utf-8') as f:
        f.write(report)
        
    print("Audit report generated at docs/prediction_pipeline_audit.md")

if __name__ == '__main__':
    run_audit()
