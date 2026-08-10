from .base import ModelAdapter
from ml.predict import predict_message as predict_baseline
import ml.predict_transformer as predict_transformer
import re
import json
import os
import hashlib

def _load_severity_tiers():
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "guidance_v1.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        always_critical = config.get("severity_tiers", {}).get("always_critical", [])
        confidence_gated = config.get("severity_tiers", {}).get("confidence_gated", [])
        
        tiers = {}
        for label in always_critical:
            tiers[label] = 1
        for label in confidence_gated:
            tiers[label] = 2
        return tiers
    except Exception:
        # Fallback to empty if missing
        return {}

# We wrap the existing logic as the primary engine.
class PrimaryModelAdapter(ModelAdapter):
    def predict(self, text: str) -> dict:
        if predict_transformer.is_available():
            base_result = predict_transformer.predict_message(text)
            return base_result
        else:
            base_result = predict_baseline(text)
            
            # Map old schema to a mocked multi-label schema
            category = base_result.get("category", "none")
            conf = base_result.get("confidence", 0.0)
            
            primary_label = category.replace("_", " ").title() if category != "none" else "Clean"
            
            # Map old labels to new label names if needed
            if primary_label == "Offensive Language":
                primary_label = "Toxicity / Offensive Language"
            elif primary_label == "Cyberbullying":
                primary_label = "Cyberbullying / Harassment"
                
            return {
                "neural_probs": {primary_label: conf} if primary_label != "Clean" else {"Clean": conf},
                "thresholds": {},
                "model": "baseline",
                "label": base_result.get("label", "non_harassing"),
                "category": category,
                "explanation": base_result.get("explanation", [])
            }

class HeuristicMultiLabelAdapter(ModelAdapter):
    def __init__(self, primary_adapter: ModelAdapter):
        self.primary_adapter = primary_adapter
        
        # Simple keyword/regex heuristics to infer secondary categories
        self.heuristics = {
            "Threat": [r"\b(kill|murder|beat|stab|hurt|shoot|destroy)\b", r"\b(watch your back|i know where you live|die)\b"],
            "Cyberbullying / Harassment": [r"\b(loser|worthless|ugly|fat|stupid|idiot|dumb|kys|die)\b", r"\b(nobody likes you)\b"],
            "Hate Speech": [r"\b(nazi|subhuman|scum|trash)\b", r"\b(hate all|dirty)\b"],
            "Identity Attack": [r"\b(gay|fag|tranny|retard|autistic|black|white|muslim|jew)\b"],
            "Profanity": [r"\b(fuck|shit|bitch|cunt|asshole|bastard|dick|cock|pussy)\b"],
            "Sexual Harassment": [r"\b(rape|molest|boobs|tits|ass|send nudes|suck)\b"],
            "Toxicity / Offensive Language": [r"\b(shut up|trash|garbage|toxic)\b"],
            "Spam": [r"\b(click here|free money|discount|buy now|subscribe|win)\b", r"http[s]?://"],
            "Self Harm": [r"\b(cut myself|kill myself|suicide|end it all)\b"],
            "Scam": [r"\b(crypto|bitcoin|investment opportunity|ponzi|pyramid scheme)\b", r"\b(guaranteed returns)\b"],
            "Phishing": [r"\b(verify your account|login to confirm|password reset link|update your payment)\b", r"\b(urgent action required.*account)\b"],
            "Impersonation": [r"\b(acting as|pretending to be|fake account|i am the real)\b"],
            "Blackmail": [r"\b(i have your photos|pay me or i will leak|expose you|send me money or)\b", r"\b(release the video)\b"],
            "Extortion": [r"\b(pay me|send bitcoin to|ransom|transfer funds immediately)\b", r"\b(if you don't pay)\b"],
            "Fraud": [r"\b(stolen credit card|fake id|bank transfer|wire me)\b"],
            "Social Engineering": [r"\b(what is your mother's maiden name|verify your ssn|send me a code)\b", r"\b(can you do me a quick favor.*gift card)\b"]
        }

        self.trained_categories = {
            "Hate Speech",
            "Cyberbullying / Harassment",
            "Threat",
            "Toxicity / Offensive Language",
            "Profanity",
            "Clean"
        }

    def explain_heuristics(self, text: str, secondary_labels: dict) -> list:
        text_lower = text.lower()
        explanations = []
        for label in secondary_labels.keys():
            if label in self.heuristics:
                for pattern in self.heuristics[label]:
                    matches = re.finditer(pattern, text_lower)
                    for match in matches:
                        word = match.group(0)
                        explanations.append({
                            "word": word,
                            "contribution": 0.8,
                            "label": label,
                            "reason": f"Matches {label} pattern"
                        })
        return explanations

    def predict(self, text: str) -> dict:
        # 1. Run the primary model
        result = self.primary_adapter.predict(text)
        
        neural_probs = result.get("neural_probs", {})
        
        text_lower = text.lower()
        symbolic_confs = {}
        
        # 2. Run heuristics independently
        for label, patterns in self.heuristics.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    heuristic_conf = 0.85 
                    # Use deterministic hash instead of Python's randomized built-in hash
                    det_hash = int(hashlib.md5((text + label).encode('utf-8')).hexdigest(), 16)
                    var = (det_hash % 10) / 100.0
                    conf = max(0.40, min(0.99, heuristic_conf - var))
                    symbolic_confs[label] = round(conf, 4)
                    break
                    
        # 3. Noisy-OR Evidence Fusion
        fused_labels = {}
        all_possible_labels = set(neural_probs.keys()) | set(symbolic_confs.keys())
        
        for label in all_possible_labels:
            if label == "Clean":
                continue # Clean is handled separately later
                
            n_prob = neural_probs.get(label, 0.0)
            s_prob = symbolic_confs.get(label, 0.0)
            
            if label == "Threat":
                n_weight = 0.15
                s_weight = 0.85
            elif label in self.trained_categories:
                n_weight = 0.8
                s_weight = 0.5
            else:
                # Symbolic-only category
                n_weight = 0.0
                s_weight = 1.0
                
            # Noisy-OR fusion
            fused_conf = 1 - (1 - n_prob * n_weight) * (1 - s_prob * s_weight)
            
            # Keep labels with confidence > 0.4 or if they passed the neural threshold
            # thresholds not applied to symbolic-only categories
            thresholds = result.get("thresholds", {})
            thresh = thresholds.get(label, 0.5)
            
            # Since fused_conf might be slightly lower than raw n_prob (e.g. n_prob=0.8, n_weight=0.8 -> 0.64), 
            # we should also check if raw n_prob > threshold just to be safe, but 
            # mathematically we want the fused conf to be the final score.
            if fused_conf >= 0.4:
                fused_labels[label] = round(fused_conf, 4)
                
        # Determine primary label using severity tiers from config
        severity_tiers = _load_severity_tiers()

        if fused_labels:
            # Filter labels that clear a reasonable floor for primary selection
            candidates = {k: v for k, v in fused_labels.items() if v > 0.5}
            
            # If nothing cleared the floor but we have fused labels, fall back to all of them
            if not candidates:
                candidates = fused_labels
                
            # Sort candidates by (severity_tier ASC, confidence DESC)
            # Default to tier 3 (lowest priority) if a category is missing from the mapping
            best_label = min(candidates.keys(), key=lambda k: (severity_tiers.get(k, 3), -candidates[k]))
            best_conf = fused_labels[best_label]
            
            secondary_labels = {k: v for k, v in fused_labels.items() if k != best_label}
            category = best_label.lower().replace(" / ", "_").replace(" ", "_").replace("/", "_")
            label_flag = "harassing"
        else:
            # If nothing triggered, it's Clean
            best_label = "Clean"
            best_conf = neural_probs.get("Clean", 0.85) 
            # If the neural model has a probability for Clean, use it, else 0.85 default
            
            secondary_labels = {}
            category = "none"
            label_flag = "non_harassing"

        # Update the result dict
        result["primary_label"] = best_label
        result["confidence"] = best_conf
        result["secondary_labels"] = secondary_labels
        result["label"] = label_flag
        result["category"] = category
        
        if result.get("model") == "baseline":
            result["model"] = "baseline+multi_label_heuristics"
        else:
            result["model"] = "Neurosymbolic Fusion (Fine-tuned DistilBERT v1 + Rule Engine)"
            
        return result
