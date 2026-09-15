import ml.predict_transformer as predict_transformer
from services.admin_service import AdminService
from ml.adapters import PrimaryModelAdapter, HeuristicMultiLabelAdapter, ConversationAdapter
from services.guidance_service import GuidanceService
from services.evidence_service import EvidenceService
from ml.adapters.threat_intel import mask_pii

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
            heuristic = HeuristicMultiLabelAdapter(primary)
            
            # Wrap with MultilingualAdapter (Phase 7A)
            try:
                from ml.adapters.multilingual import MultilingualAdapter
                cls._adapter = MultilingualAdapter(heuristic)
            except ImportError as e:
                # Fallback if dependencies not installed
                print(f"Warning: Multilingual support not available: {e}")
                cls._adapter = heuristic
                
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
            result["evidence_plan"] = EvidenceService.get_action_plan(result)
            
        return result

    @staticmethod
    def extract_threat_signal_summary(threat_signals: dict) -> dict:
        categories = set()
        if threat_signals.get("social_engineering", {}).get("detected"):
            categories.add("social_engineering")
        if threat_signals.get("urgency", {}).get("detected"):
            categories.add("urgency")
        if threat_signals.get("brand_impersonation", {}).get("detected"):
            categories.add("brand_impersonation")
            
        return {
            "detected": len(categories) > 0,
            "categories": sorted(list(categories)),
            "count": len(categories)
        }

    @staticmethod
    def _add_threat_intel_reasons(reasons: list, threat_signals: dict, include_urgency: bool = True):
        for ip_url in threat_signals.get("ip_based_urls", []):
            if ip_url.get("reason") not in reasons:
                reasons.append(ip_url.get("reason"))
        for short_url in threat_signals.get("url_shorteners", []):
            if short_url.get("reason") not in reasons:
                reasons.append(short_url.get("reason"))
                
        if threat_signals.get("social_engineering", {}).get("detected"):
            for ind in threat_signals["social_engineering"]["indicators"]:
                ind_clean = ind.replace("_", "-")
                msg = f"A potential {ind_clean} indicator was detected."
                if msg not in reasons:
                    reasons.append(msg)
                    
        if include_urgency and threat_signals.get("urgency", {}).get("detected"):
            count = threat_signals["urgency"].get("count", 0)
            if count > 1:
                reasons.append("Multiple urgency indicators were detected.")
            elif count == 1:
                reasons.append("An urgency indicator was detected.")
                
        if threat_signals.get("brand_impersonation", {}).get("detected"):
            for b in threat_signals["brand_impersonation"].get("brands", []):
                msg = f"A potential brand impersonation indicator involving {b} was detected."
                if msg not in reasons:
                    reasons.append(msg)
                    
        if threat_signals.get("dangerous_schemes"):
            msg = "A potentially dangerous URL scheme was detected."
            if msg not in reasons:
                reasons.append(msg)

    @staticmethod
    def attach_risk_and_similarity(result: dict, text_for_embedding: str) -> dict:
        # Use translated text for similarity matching if translation occurred
        if result.get("multilingual_analysis", {}).get("translation_status") == "success" and "_translated_text" in result:
            text_for_embedding = result["_translated_text"]

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
            
        result["evidence_plan"] = EvidenceService.get_action_plan(result)

        # Deterministic Explainability (Why was this flagged?)
        reasons = []
        def add_reason(r):
            if r not in reasons:
                reasons.append(r)

        if primary_label.lower() not in ["none", "clean", "safe"]:
            add_reason(f"Content classified as {primary_label.title()}.")
            
        for sec_cat in secondary_labels.keys():
            add_reason(f"Indicators of {sec_cat.title()} detected.")
            
        if "pii_categories" in result and result["pii_categories"]:
            cats = sorted(list(set([c.replace("_", " ").title() for c in result["pii_categories"]])))
            add_reason(f"Personally Identifiable Information (PII) detected: {', '.join(cats)}.")
            
        if result.get("malicious_urls"):
            add_reason("Suspicious or malicious link(s) detected.")
            
        if "threat_intel" in result:
            emails = result["threat_intel"].get("emails", [])
            if any(e.get("breach_count", 0) > 0 for e in emails):
                add_reason("An email address in the submitted content appears in known data-breach records.")
                
            threat_signals = result["threat_intel"].get("threat_signals", {})
            for ip_url in threat_signals.get("ip_based_urls", []):
                add_reason(ip_url.get("reason"))
            for short_url in threat_signals.get("url_shorteners", []):
                add_reason(short_url.get("reason"))
                
            if threat_signals.get("social_engineering", {}).get("detected"):
                for ind in threat_signals["social_engineering"]["indicators"]:
                    ind_clean = ind.replace("_", "-")
                    add_reason(f"A potential {ind_clean} indicator was detected.")
                    
            if threat_signals.get("urgency", {}).get("detected"):
                count = threat_signals["urgency"].get("count", 0)
                if count > 1:
                    add_reason("Multiple urgency indicators were detected.")
                elif count == 1:
                    add_reason("An urgency indicator was detected.")
                    
            if threat_signals.get("brand_impersonation", {}).get("detected"):
                brands = threat_signals["brand_impersonation"].get("brands", [])
                for b in brands:
                    add_reason(f"A potential brand impersonation indicator involving {b} was detected.")
                    
            if threat_signals.get("dangerous_schemes"):
                add_reason("A potentially dangerous URL scheme was detected.")
                
            job_scam = result["threat_intel"].get("job_scam_signals", {})
            if job_scam.get("detected"):
                if job_scam.get("detected_suspicious"):
                    add_reason("Suspicious recruitment or job offer indicators detected.")
                elif job_scam.get("recruitment_context"):
                    add_reason("A recruitment-related document was detected.")
                
                for ind in job_scam.get("indicators", []):
                    if ind == "payment_before_joining":
                        add_reason("A payment-related recruitment indicator was detected.")
                    elif ind == "suspicious_communication":
                        add_reason("A suspicious recruitment contact indicator was detected.")
                    elif ind == "suspicious_url":
                        add_reason("A suspicious recruitment URL was detected.")
                    elif ind == "unusual_payment_method":
                        add_reason("An unusual payment method request was detected.")
                
        if not reasons and result["risk_score"] > 0:
            add_reason("Flagged by automated safety checks.")
            
        result["flagging_reasons"] = reasons
        
        threat_signals = result.get("threat_intel", {}).get("threat_signals", {})
        result["threat_signal_summary"] = PredictionService.extract_threat_signal_summary(threat_signals)

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
            masked_texts = [mask_pii(m["text"]) for m in result["messages"]]
            ai_summary = summarize_conversation(
                masked_texts, 
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
            
        result["evidence_plan"] = EvidenceService.get_action_plan(result)

        # Deterministic Explainability (Why was this flagged?) for Conversation
        reasons = []
        def add_reason(r):
            if r not in reasons:
                reasons.append(r)

        if primary_label.lower() not in ["none", "clean", "safe"]:
            add_reason(f"Conversation classified as {primary_label.title()}.")
            
        for msg in result.get("messages", []):
            for sec_cat in msg.get("secondary_labels", {}).keys():
                add_reason(f"Indicators of {sec_cat.title()} detected.")
                
        pii_cats = set()
        for msg in result.get("messages", []):
            if msg.get("pii_categories"):
                for c in msg["pii_categories"]:
                    pii_cats.add(c.replace("_", " ").title())
        if pii_cats:
            add_reason(f"Personally Identifiable Information (PII) detected: {', '.join(sorted(list(pii_cats)))}.")
                
        if result.get("malicious_urls"):
            add_reason("Suspicious or malicious link(s) detected.")
            
        has_multiple_urgency = False
        has_single_urgency = False
        
        total_urgency_count = 0
        for msg in result.get("messages", []):
            threat_signals = msg.get("threat_intel", {}).get("threat_signals", {})
            if threat_signals.get("urgency", {}).get("detected"):
                total_urgency_count += threat_signals["urgency"].get("count", 0)
                
        if total_urgency_count > 1:
            has_multiple_urgency = True
        elif total_urgency_count == 1:
            has_single_urgency = True
            
        for msg in result.get("messages", []):
            if "threat_intel" in msg:
                emails = msg["threat_intel"].get("emails", [])
                if any(e.get("breach_count", 0) > 0 for e in emails):
                    add_reason("An email address in the submitted content appears in known data-breach records.")
                    
                threat_signals = msg["threat_intel"].get("threat_signals", {})
                for ip_url in threat_signals.get("ip_based_urls", []):
                    add_reason(ip_url.get("reason"))
                for short_url in threat_signals.get("url_shorteners", []):
                    add_reason(short_url.get("reason"))
                    
                if threat_signals.get("social_engineering", {}).get("detected"):
                    for ind in threat_signals["social_engineering"]["indicators"]:
                        ind_clean = ind.replace("_", "-")
                        add_reason(f"A potential {ind_clean} indicator was detected.")
                        
                if threat_signals.get("brand_impersonation", {}).get("detected"):
                    brands = threat_signals["brand_impersonation"].get("brands", [])
                    for b in brands:
                        add_reason(f"A potential brand impersonation indicator involving {b} was detected.")
                        
                if threat_signals.get("dangerous_schemes"):
                    add_reason("A potentially dangerous URL scheme was detected.")
                    
                job_scam = msg["threat_intel"].get("job_scam_signals", {})
                if job_scam.get("detected"):
                    if job_scam.get("detected_suspicious"):
                        add_reason("Suspicious recruitment or job offer indicators detected.")
                    elif job_scam.get("recruitment_context"):
                        add_reason("A recruitment-related document was detected.")
                    
                    for ind in job_scam.get("indicators", []):
                        if ind == "payment_before_joining":
                            add_reason("A payment-related recruitment indicator was detected.")
                        elif ind == "suspicious_communication":
                            add_reason("A suspicious recruitment contact indicator was detected.")
                        elif ind == "suspicious_url":
                            add_reason("A suspicious recruitment URL was detected.")
                        elif ind == "unusual_payment_method":
                            add_reason("An unusual payment method request was detected.")
            
        if has_multiple_urgency:
            add_reason("Multiple urgency indicators were detected.")
        elif has_single_urgency:
            add_reason("An urgency indicator was detected.")
            
        if not reasons and result["conversation_risk"] > 0:
            add_reason("Flagged by automated safety checks.")
            
        result["flagging_reasons"] = reasons
        
        # Aggregate threat_signals for conversation summary
        agg_threat_signals = {
            "social_engineering": {"detected": False},
            "urgency": {"detected": False},
            "brand_impersonation": {"detected": False}
        }
        for msg in result.get("messages", []):
            ts = msg.get("threat_intel", {}).get("threat_signals", {})
            if ts.get("social_engineering", {}).get("detected"):
                agg_threat_signals["social_engineering"]["detected"] = True
            if ts.get("urgency", {}).get("detected"):
                agg_threat_signals["urgency"]["detected"] = True
            if ts.get("brand_impersonation", {}).get("detected"):
                agg_threat_signals["brand_impersonation"]["detected"] = True

        result["threat_signal_summary"] = PredictionService.extract_threat_signal_summary(agg_threat_signals)
            
        return result
