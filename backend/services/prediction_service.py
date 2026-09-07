import ml.predict_transformer as predict_transformer
from services.admin_service import AdminService
from ml.adapters import PrimaryModelAdapter, HeuristicMultiLabelAdapter, ConversationAdapter
from services.guidance_service import GuidanceService

try:
    import ml.explain as explain_module
    _explain_available = True
except Exception:
    _explain_available = False

_similarity_available = False
try:
    from ml.similarity import find_similar_reports
    _similarity_available = True
except Exception:
    pass

CATEGORY_RISK_BASE = {
    "Threat": 90,
    "Extortion": 90,
    "Blackmail": 85,
    "Self Harm": 90,
    "Hate Speech": 80,
    "Cyberbullying / Harassment": 75,
    "Sexual Harassment": 75,
    "Identity Attack": 70,
    "Phishing": 90,
    "Scam": 85,
    "Fraud": 85,
    "Impersonation": 70,
    "Social Engineering": 75,
    "Spam": 60,
    "Profanity": 50,
    "Toxicity / Offensive Language": 50,
    "Clean": 5,
    "hate_speech": 80,
    "offensive_language": 50,
    "none": 5
}

class PredictionService:
    _adapter = None
    _conversation_adapter = None

    @classmethod
    def get_adapter(cls):
        if cls._adapter is None:
            primary = PrimaryModelAdapter()
            cls._adapter = HeuristicMultiLabelAdapter(primary)
        return cls._adapter

    @classmethod
    def get_conversation_adapter(cls):
        if cls._conversation_adapter is None:
            cls._conversation_adapter = ConversationAdapter(cls.get_adapter())
        return cls._conversation_adapter

    @staticmethod
    def get_active_model_name() -> str:
        return "distilbert+multi_label_heuristics" if predict_transformer.is_available() else "baseline+multi_label_heuristics"

    @staticmethod
    def compute_risk_score(primary_category: str, primary_conf: float, secondary_categories: dict) -> float:
        # Base severity of primary
        base = CATEGORY_RISK_BASE.get(primary_category, 5)
        score = base * primary_conf
        
        # Add risk for secondary categories
        for sec_cat, sec_conf in secondary_categories.items():
            sec_base = CATEGORY_RISK_BASE.get(sec_cat, 20)
            score += (sec_base * sec_conf * 0.2) # 20% weight for secondary labels
            
        # Add bonus for multi-vector attacks
        if len(secondary_categories) > 0:
            score += len(secondary_categories) * 5
            
        return round(min(100, max(0, score)), 1)

    @staticmethod
    def classify_text(text: str) -> dict:
        result = PredictionService.get_adapter().predict(text)
        
        # Explainability for Primary Label if it maps to the old classes (only works if model is baseline)
        if _explain_available and "baseline" in result.get("model", ""):
            CATEGORY_TO_CLASS = {"hate_speech": 0, "offensive_language": 1, "none": 2}
            cat = result.get("category")
            if cat in CATEGORY_TO_CLASS:
                result["explanation"] = explain_module.explain_prediction(
                    text, CATEGORY_TO_CLASS[cat], top_n=5
                )
        else:
            result["explanation"] = []
            
        # Append heuristic explanations for secondary labels
        adapter = PredictionService.get_adapter()
        if hasattr(adapter, "explain_heuristics") and result.get("secondary_labels"):
            result["explanation"].extend(adapter.explain_heuristics(text, result["secondary_labels"]))
            
        return result

    @staticmethod
    def attach_risk_and_similarity(result: dict, text_for_embedding: str) -> dict:
        result["risk_score"] = PredictionService.compute_risk_score(
            result.get("primary_label", result.get("category", "none")),
            result.get("confidence", 0),
            result.get("secondary_labels", {})
        )

        if result.get("label") == "harassing" and _similarity_available:
            try:
                existing = AdminService.get_all_flagged()
                matches, embedding = find_similar_reports(text_for_embedding, existing)
                result["embedding"] = embedding
                if matches:
                    result["similar_reports"] = matches[:3]
                    result["cluster_id"] = f"cluster-{hash(matches[0]['text_preview']) % 10000:04d}"
            except Exception:
                pass 
                
        # Attach structured guidance
        platform = result.get("platform", "generic")
        primary_label = result.get("primary_label", result.get("category", "none"))
        primary_conf = result.get("confidence", 0)
        secondary_labels = result.get("secondary_labels", {})
        
        result["guidance"] = GuidanceService.get_guidance(
            primary_label, primary_conf, secondary_labels, result["risk_score"], platform
        )

        result["severity_tier"] = GuidanceService.compute_severity(
            result["guidance"].get("show_critical_resources", False),
            result["risk_score"]
        )

        # Unified Threat Analysis (Phase 1)
        result["threat_score"] = result["risk_score"]
        result["safety_status"] = "Safe" if result["severity_tier"] == "Safe" else "At Risk"
        result["evidence"] = text_for_embedding if result["severity_tier"] != "Safe" else "No specific threat evidence detected."

        if "threat_intel" in result and "malicious_urls" in result["threat_intel"]:
            result["malicious_urls"] = result["threat_intel"]["malicious_urls"]
        elif "malicious_urls" not in result:
            result["malicious_urls"] = []

        return result

    @staticmethod
    def analyze_conversation(messages: list) -> dict:
        result = PredictionService.get_conversation_adapter().predict_conversation(messages)
        
        # Aggregate malicious_urls from all messages
        all_malicious_urls = []
        for msg in result.get("messages", []):
            if "threat_intel" in msg and "malicious_urls" in msg["threat_intel"]:
                # To avoid duplicates if multiple messages have the same URL
                for m_url in msg["threat_intel"]["malicious_urls"]:
                    if not any(u["url"] == m_url["url"] for u in all_malicious_urls):
                        all_malicious_urls.append(m_url)
        result["malicious_urls"] = all_malicious_urls
        
        try:
            from ml.summarize import summarize_conversation
            ai_summary = summarize_conversation(
                [m["text"] for m in result["messages"]], 
                result["conversation_risk"]
            )
            # Remove the old recommended_action from AI summary
            if "recommended_action" in ai_summary:
                del ai_summary["recommended_action"]
            result["ai_summary"] = ai_summary
        except Exception:
            result["ai_summary"] = {
                "overall_sentiment": "Unknown",
                "harassment_pattern": "Unable to summarize."
            }
            
        # Determine platform if provided
        platform = messages[0].get("platform", "generic") if messages else "generic"
        
        # We need primary and secondary labels for the entire conversation to pass to get_guidance.
        # Let's aggregate them from the highest risk message.
        highest_risk_msg = max(result["messages"], key=lambda m: m.get("risk_score", 0), default={})
        primary_label = highest_risk_msg.get("primary_label", highest_risk_msg.get("category", "none"))
        primary_conf = highest_risk_msg.get("confidence", 0)
        secondary_labels = highest_risk_msg.get("secondary_labels", {})
        
        result["guidance"] = GuidanceService.get_guidance(
            primary_label, primary_conf, secondary_labels, result["conversation_risk"], platform
        )

        result["severity_tier"] = GuidanceService.compute_severity(
            result["guidance"].get("show_critical_resources", False),
            result["conversation_risk"]
        )

        # Unified Threat Analysis (Phase 1)
        result["threat_score"] = result["conversation_risk"]
        result["safety_status"] = "Safe" if result["severity_tier"] == "Safe" else "At Risk"
        result["evidence"] = highest_risk_msg.get("text", "No specific threat evidence detected.") if result["severity_tier"] != "Safe" else "No specific threat evidence detected."
            
        return result
