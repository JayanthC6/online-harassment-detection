import json
import os

class EvidenceService:
    _playbooks = None

    @classmethod
    def load_playbooks(cls):
        if cls._playbooks is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "evidence_playbooks.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cls._playbooks = json.load(f)
            else:
                cls._playbooks = {}
        return cls._playbooks

    @classmethod
    def get_action_plan(cls, prediction_result):
        playbooks = cls.load_playbooks()
        
        primary_label = prediction_result.get("primary_label", "none")
        severity_tier = prediction_result.get("severity_tier", "Low")
        source = prediction_result.get("platform", "generic")
        pii_categories = prediction_result.get("pii_categories", [])
        is_conversation = "messages" in prediction_result
        
        # Initialize the plan sections with general defaults
        general = playbooks.get("general", {})
        checklist = list(general.get("evidence_checklist", []))
        preservation = list(general.get("preservation_guidance", []))
        safety = list(general.get("safety_actions", []))
        recommended = list(general.get("recommended_steps", []))
        
        # Apply specific overrides based on label
        if primary_label in playbooks:
            specific = playbooks[primary_label]
            if "evidence_checklist" in specific:
                checklist = specific["evidence_checklist"] + checklist
            if "preservation_guidance" in specific:
                preservation = specific["preservation_guidance"] + preservation
            if "safety_actions" in specific:
                safety = specific["safety_actions"] + safety
            if "recommended_steps" in specific:
                recommended = specific["recommended_steps"] + recommended
                
        # Apply source-specific rules (e.g. whatsapp)
        if source.lower() in playbooks:
            src_specific = playbooks[source.lower()]
            if "evidence_checklist" in src_specific:
                checklist = src_specific["evidence_checklist"] + checklist
            if "preservation_guidance" in src_specific:
                preservation = src_specific["preservation_guidance"] + preservation
                
        # Apply PII exposed rules
        if pii_categories:
            pii_specific = playbooks.get("pii_exposed", {})
            if "safety_actions" in pii_specific:
                safety = pii_specific["safety_actions"] + safety
                
        # Deduplicate lists while preserving order
        def dedupe(seq):
            seen = set()
            return [x for x in seq if not (x in seen or seen.add(x))]

        # Compile why_flagged
        count = len(prediction_result.get("messages", [])) if is_conversation else 1
        msg_text = "messages" if count > 1 else "message"
        why_flagged = f"Detected {count} {msg_text} involving {primary_label.replace('_', ' ')} with {severity_tier} risk severity."
        
        # Determine a simple case summary
        case_summary = f"{severity_tier} Risk Incident - {primary_label.replace('_', ' ').title()}"
        
        return {
            "case_summary": case_summary,
            "why_flagged": why_flagged,
            "evidence_checklist": dedupe(checklist),
            "preservation_guidance": dedupe(preservation),
            "safety_actions": dedupe(safety),
            "recommended_steps": dedupe(recommended)
        }
