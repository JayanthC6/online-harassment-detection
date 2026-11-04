"""
ShieldAI Complaint Summarization Service.

Generates structured incident summaries using either:
1. Groq's LLM API (if GROQ_API_KEY is configured in .env).
2. Deterministic, high-fidelity rule-based engine (offline fallback).

Ensures 100% offline reliability without crashing if API keys are missing or calls fail.
"""
import os
import json
import re

def _generate_deterministic_summary(text: str, category: str, confidence: float, risk_score: float = 0.0, persona: str = "user") -> dict:
    """Fallback generator that constructs factual, high-quality incident summaries without external API calls."""
    cat = (category or "").lower().strip()
    conf_pct = f"{confidence * 100:.1f}%" if confidence else "high confidence"

    if cat in ["threat", "physical_threat"]:
        desc = f"Direct physical threat detected. The communication conveys explicit threats of bodily violence or harm against the recipient with {conf_pct}."
        action = "Preserve full screenshots and contact emergency services (112) immediately if in imminent danger. Do not confront or meet the sender."
        severity = "high"
    elif cat in ["sextortion", "blackmail", "extortion"]:
        desc = "Extortion and blackmail detected. The sender attempts financial coercion by alleging possession of compromising material and demanding ransom. Many such claims are mass-sent automated bluffs."
        action = "Do not transfer cryptocurrency or funds. Preserve timestamped screenshots and report the incident to helpline 1930 and https://cybercrime.gov.in."
        severity = "high"
    elif cat in ["phishing", "credential_harvesting"]:
        desc = "Credential phishing attempt detected. The message employs artificial urgency or fake account-suspension notices to trick the recipient into visiting unverified links."
        action = "Do not click embedded links, verify OTPs, or share credentials. Block the sender and report the fraudulent link."
        severity = "high" if risk_score >= 70 else "medium"
    elif cat in ["scam", "fraud", "lottery_scam"]:
        desc = "Fraudulent scam detected. The message promises bogus lottery winnings, rewards, or refunds to solicit advance processing fees or gift cards."
        action = "Never send money, crypto, or gift card codes. Block the sender and file an alert with cybercrime authorities."
        severity = "medium"
    elif cat in ["hate_speech"]:
        desc = "Hate speech and targeted group hostility detected. The content attacks protected personal or demographic identity characteristics."
        action = "Document evidence, report the user to platform moderators, and block further communications."
        severity = "high" if risk_score >= 75 else "medium"
    elif cat in ["offensive_language", "abusive_language", "cyberbullying_harassment", "harassment"]:
        desc = "Targeted harassment and abusive language detected containing aggressive insults or hostile pressure."
        action = "Block the sender and preserve communication history in case of persistent escalation."
        severity = "medium" if risk_score >= 50 else "low"
    elif cat in ["none", "clean"]:
        desc = "Communication evaluated as safe and non-threatening. No high-risk harassment or fraud indicators detected."
        action = "No protective intervention required."
        severity = "low"
    else:
        desc = f"Flagged message classified under {category.replace('_', ' ').title()} with {conf_pct}."
        action = "Review the flagged text and take appropriate precautionary measures based on sender credibility."
        severity = "medium" if risk_score >= 50 else "low"

    summary_text = f"{desc} Recommended Action: {action}"

    category_labels = {
        "hate_speech": "Hate Speech",
        "offensive_language": "Offensive Language",
        "abusive_language": "Abusive Language",
        "cyberbullying_harassment": "Harassment",
        "threat": "Threat",
        "sextortion": "Sextortion",
        "phishing": "Phishing",
        "scam": "Scam",
        "none": "Clean",
        "clean": "Clean",
    }

    return {
        "summary": summary_text,
        "incident_description": desc,
        "category": category_labels.get(cat, category.title() if category else "Unknown"),
        "severity": severity,
        "suggested_action": action,
        "engine": "rules"
    }


def summarize_complaint(text: str, category: str, confidence: float, risk_score: float = 0.0, persona: str = "user") -> dict:
    """
    Generate a structured incident summary using Groq LLM (if configured) or the rule-based fallback.
    Never raises an unhandled exception or causes a 500 error.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return _generate_deterministic_summary(text, category, confidence, risk_score, persona)

    try:
        from groq import Groq
        from services.guidance_service import GuidanceService

        client = Groq(api_key=api_key)

        guidance_data = GuidanceService.get_guidance(category, confidence, {}, risk_score)
        severity = GuidanceService.compute_severity(
            guidance_data.get("show_critical_resources", False),
            risk_score
        )
        fallback_action = guidance_data.get("report_instructions", "No immediate action required.")

        model_name = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

        prompt = f"""Analyze the following reported incident:

Reported text: "{text}"
Detected Category: {category}

Please provide a JSON object with exactly two keys:
1. "incident_description": A 2-3 sentence factual summary of what happened.
2. "suggested_action": Recommended tactical next steps for this incident.

Respond ONLY with valid JSON."""

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a cyber safety threat analyst. Output strict JSON."},
                {"role": "user", "content": prompt},
            ],
            model=model_name,
            temperature=0.3,
            max_tokens=300,
            response_format={"type": "json_object"}
        )

        content = chat_completion.choices[0].message.content.strip()
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        data = json.loads(content)
        incident_description = data.get("incident_description", "")
        suggested_action = data.get("suggested_action", "")

        if not incident_description:
            return _generate_deterministic_summary(text, category, confidence, risk_score, persona)

        summary_text = f"{incident_description} Recommended Action: {suggested_action}"

        category_labels = {
            "hate_speech": "Hate Speech",
            "offensive_language": "Offensive Language",
            "none": "Clean",
        }

        return {
            "summary": summary_text,
            "incident_description": incident_description,
            "category": category_labels.get(category, category.title() if category else "Unknown"),
            "severity": severity or "medium",
            "suggested_action": suggested_action,
            "engine": "groq"
        }
    except Exception as e:
        # Fall back gracefully to rule-based summary without failing
        print(f"Groq summarize error (falling back to rules): {e}")
        return _generate_deterministic_summary(text, category, confidence, risk_score, persona)


def summarize_conversation(messages: list, risk_score: float) -> dict:
    """Summarize a multi-message conversation with safe offline fallback."""
    if risk_score >= 75:
        rec = "Immediate intervention recommended. Ban or suspend the offending participant."
        pattern = "Severe harassment or escalating threats identified across messages."
        sentiment = "Hostile"
    elif risk_score >= 40:
        rec = "Review closely. Issue a warning to the offending participant."
        pattern = "Moderate interpersonal friction and offensive language."
        sentiment = "Aggressive"
    else:
        rec = "No immediate action required. Monitor for future escalation."
        pattern = "No sustained harassment pattern."
        sentiment = "Neutral"

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {
            "overall_sentiment": sentiment,
            "harassment_pattern": pattern,
            "recommended_action": rec
        }

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        chat_text = "\n".join([f"Message {i+1}: {msg}" for i, msg in enumerate(messages)])
        model_name = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

        prompt = f"""Analyze the following conversation context.
Provide a very brief assessment of:
1. Overall sentiment (e.g. Hostile, Aggressive, Neutral)
2. Harassment pattern (e.g. Escalating threats, Repeated insults, None)

Conversation:
{chat_text}

Respond in this exact JSON format:
{{"overall_sentiment": "...", "harassment_pattern": "..."}}
Do not include any other text.
"""
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a moderation AI that outputs strict JSON."},
                {"role": "user", "content": prompt},
            ],
            model=model_name,
            temperature=0.3,
            max_tokens=150,
            response_format={"type": "json_object"}
        )
        content = chat_completion.choices[0].message.content.strip()
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        data = json.loads(content)

        return {
            "overall_sentiment": data.get("overall_sentiment", sentiment),
            "harassment_pattern": data.get("harassment_pattern", pattern),
            "recommended_action": rec
        }
    except Exception as e:
        print(f"Summarize Conversation Error (falling back to rules): {e}")
        return {
            "overall_sentiment": sentiment,
            "harassment_pattern": pattern,
            "recommended_action": rec
        }
