import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "guidance_v1.json")

class GuidanceService:
    _config = None

    @classmethod
    def _load_config(cls):
        if cls._config is None:
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cls._config = json.load(f)
            except Exception as e:
                # Fallback empty config if missing
                cls._config = {
                    "platforms": {"generic": {"name": "General", "report_instructions": "Use native reporting.", "block_instructions": "Block the user."}},
                    "evidence_checklist": [],
                    "critical_resources": {},
                    "severity_tiers": {"always_critical": [], "confidence_gated": []}
                }
        return cls._config

    @classmethod
    def get_guidance(cls, primary_label, primary_confidence, secondary_labels, risk_score, platform="generic"):
        config = cls._load_config()
        
        # Determine platform
        if platform not in config.get("platforms", {}):
            platform = "generic"
            
        platform_data = config.get("platforms", {}).get(platform, {})
        
        # Determine if critical resources should be shown
        show_critical_resources = False
        always_critical = config.get("severity_tiers", {}).get("always_critical", [])
        confidence_gated = config.get("severity_tiers", {}).get("confidence_gated", [])
        
        # Build a dict of all labels and their confidences
        all_labels = {primary_label: primary_confidence}
        if secondary_labels:
            all_labels.update(secondary_labels)
            
        # Check against severity tiers
        for label, conf in all_labels.items():
            if label in always_critical:
                show_critical_resources = True
                break
            if label in confidence_gated:
                if conf >= 0.7 or risk_score >= 80:
                    show_critical_resources = True
                    break
                    
        # Also trigger if risk_score is intrinsically very high
        if risk_score >= 80:
            show_critical_resources = True
            
        return {
            "platform_name": platform_data.get("name", "General"),
            "report_instructions": platform_data.get("report_instructions", ""),
            "block_instructions": platform_data.get("block_instructions", ""),
            "evidence_checklist": config.get("evidence_checklist", []),
            "show_critical_resources": show_critical_resources,
            "critical_resources": config.get("critical_resources", {}) if show_critical_resources else None
        }

    @classmethod
    def compute_severity(cls, show_critical_resources, risk_score):
        """Compute standardized severity tier based on risk score and critical flags."""
        if show_critical_resources:
            return "Critical"
        elif risk_score >= 60:
            return "High"
        elif risk_score >= 30:
            return "Medium"
        elif risk_score >= 15:
            return "Low"
        else:
            return "Safe"

