import json
import os

class EvidenceService:
    _playbooks = None
    _playbooks_mtime = None

    @classmethod
    def load_playbooks(cls):
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "evidence_playbooks.json"
        )
        if os.path.exists(config_path):
            mtime = os.path.getmtime(config_path)
            if cls._playbooks is None or cls._playbooks_mtime != mtime:
                with open(config_path, "r", encoding="utf-8") as f:
                    cls._playbooks = json.load(f)
                cls._playbooks_mtime = mtime
        else:
            if cls._playbooks is None:
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

        # ── Job / Recruitment Intelligence override ──────────────────────────
        # Read job_scam_signals from result.threat_intel.job_scam_signals
        # (the canonical location set by PredictionService / threat_intel adapter).
        # This check runs BEFORE the Safe-wipe guard so that a suspicious
        # recruitment signal is never silently presented as "No immediate safety
        # actions required."  Risk score is NOT changed here.
        _threat_intel = prediction_result.get("threat_intel") or {}
        _job_scam = _threat_intel.get("job_scam_signals") or {}
        _is_suspicious_recruitment = bool(_job_scam.get("detected_suspicious"))

        if _is_suspicious_recruitment:
            rec_playbook = playbooks.get("job_scam_suspicious", {})

            # Human-readable indicator labels
            _indicator_map = {
                "payment_before_joining":   "Payment demanded before joining",
                "suspicious_communication": "Suspicious communication channel",
                "unusual_payment_method":   "Unusual payment method requested",
                "suspicious_url":           "Suspicious or malicious URL present",
                "urgency_pressure":         "Urgency / pressure tactics detected",
            }
            raw_indicators = _job_scam.get("indicators", [])
            indicator_bullets = [
                _indicator_map.get(i, i.replace("_", " ").title())
                for i in raw_indicators
            ]

            assessment = _job_scam.get(
                "assessment", "Potentially Suspicious Recruitment Document"
            )

            case_summary = "Potentially Suspicious Recruitment Incident"
            why_flagged = (
                "Recruitment-related content contains indicators that may be "
                "associated with fraudulent or suspicious job offers."
            )

            checklist = rec_playbook.get("evidence_checklist", [
                "Original job-offer message or document",
                "Sender contact information (phone, email, Telegram handle)",
                "Any payment receipt or demand details",
                "Screenshots with timestamps visible",
            ])

            preservation = rec_playbook.get("preservation_guidance", [
                "Do not delete the original message or document.",
                "Take screenshots immediately with timestamps visible.",
                "Save any links or attachments without clicking them.",
                "Do not alter or delete any communication history.",
            ])

            # Indicator-specific bullets first, then general safety actions
            indicator_safety = [
                f"Recruitment indicator detected: {b}." for b in indicator_bullets
            ]
            base_safety = rec_playbook.get("safety_actions", [
                "Do not make any payment to secure or process the job offer.",
                "Verify the employer using contact information obtained independently from the message.",
                "Avoid sharing financial credentials, identity documents, OTPs, or other sensitive information until verified.",
                "Do not communicate exclusively through personal messaging apps (e.g. Telegram, WhatsApp) if asked to do so.",
            ])
            safety = indicator_safety + base_safety

            recommended = rec_playbook.get("recommended_steps", [
                "Search for the company independently through official channels (website, LinkedIn, government registries).",
                "Report the message to your local cybercrime authority or consumer protection body.",
                f"Note the recruiter's assessment: {assessment}",
            ])

            def dedupe(seq):
                seen = set()
                return [x for x in seq if not (x in seen or seen.add(x))]

            return {
                "case_summary":          case_summary,
                "why_flagged":           why_flagged,
                "evidence_checklist":    dedupe(checklist),
                "preservation_guidance": dedupe(preservation),
                "safety_actions":        dedupe(safety),
                "recommended_steps":     dedupe(recommended),
            }
        # ─────────────────────────────────────────────────────────────────────

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

        # Clear out inappropriate threat responses if the content is safe
        if severity_tier == "Safe" or primary_label.lower() in ["none", "clean"]:
            checklist = []
            preservation = []
            safety = []
            recommended = ["No specific action required. Continue as normal."]

        # Deduplicate lists while preserving order
        def dedupe(seq):
            seen = set()
            return [x for x in seq if not (x in seen or seen.add(x))]

        # Compile why_flagged
        count = len(prediction_result.get("messages", [])) if is_conversation else 1
        msg_text = "messages" if count > 1 else "message"
        why_flagged = (
            f"Detected {count} {msg_text} involving "
            f"{primary_label.replace('_', ' ')} with {severity_tier} risk severity."
        )

        # Determine a simple case summary
        case_summary = (
            f"{severity_tier} Risk Incident - "
            f"{primary_label.replace('_', ' ').title()}"
        )

        return {
            "case_summary":          case_summary,
            "why_flagged":           why_flagged,
            "evidence_checklist":    dedupe(checklist),
            "preservation_guidance": dedupe(preservation),
            "safety_actions":        dedupe(safety),
            "recommended_steps":     dedupe(recommended),
        }
