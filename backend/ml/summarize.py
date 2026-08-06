"""
Groq-powered complaint summarization.

Generates a structured summary of a flagged harassment report using Groq's
LLM API (llama-3.1-8b-instant). The Groq call is ONLY for summarizing and
structuring the user's own text — it does NOT generate legal citations,
case law references, or legal advice.

The "suggested_action" field is computed by rule-based Python code AFTER the
Groq call, NOT inside it.

Requires GROQ_API_KEY in .env (never hardcoded or committed).
"""
import os
import json


# ── Rule-based action suggestions (NOT LLM-generated) ──
ACTION_MAP = {
    "hate_speech": "Report to platform administrators immediately. Preserve all evidence including screenshots and timestamps. Consider reporting to relevant authorities if the content contains direct threats.",
    "offensive_language": "Document the incident with screenshots and timestamps. Report the content through the platform's reporting mechanism. Block the offending user if the platform supports it.",
    "none": "No immediate action required. Continue monitoring for patterns of escalation.",
}

SEVERITY_MAP = {
    "hate_speech": "high",
    "offensive_language": "medium",
    "none": "low",
}


def summarize_complaint(text: str, category: str, confidence: float) -> dict:
    """
    Generate a structured incident summary using Groq for text summarization
    and rule-based logic for severity/action.

    Returns:
        {
            "incident_description": str,  # Groq-generated summary
            "category": str,              # human-readable category
            "severity": str,              # rule-based: high/medium/low
            "suggested_action": str,      # rule-based, NOT LLM-generated
        }
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment. Add it to backend/.env")

    from groq import Groq

    client = Groq(api_key=api_key)

    # The prompt explicitly forbids legal advice / citations
    prompt = f"""Summarize the following reported incident in 2-3 clear sentences.
Describe what happened based only on the text provided. Be factual and concise.

IMPORTANT: Do NOT reference any laws, legal codes, statutes, regulations,
or provide any form of legal advice. Do NOT generate legal citations.
Only describe what the text says in plain language.

Reported text: "{text}"

Respond with ONLY the summary paragraph, nothing else."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a content moderation assistant that summarizes reported incidents. You never provide legal advice or cite laws.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=200,
        )
        incident_description = chat_completion.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"Groq API call failed: {str(e)}")

    # Category label mapping
    category_labels = {
        "hate_speech": "Hate Speech",
        "offensive_language": "Offensive Language",
        "none": "Not Harassing",
    }

    return {
        "incident_description": incident_description,
        "category": category_labels.get(category, category),
        "severity": SEVERITY_MAP.get(category, "low"),
        "suggested_action": ACTION_MAP.get(category, ACTION_MAP["none"]),
    }

def summarize_conversation(messages: list, risk_score: float) -> dict:
    """
    Summarize a multi-message conversation.
    Returns: { overall_sentiment, harassment_pattern, recommended_action }
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # Fallback if no API key
        return {
            "overall_sentiment": "Negative" if risk_score > 40 else "Neutral",
            "harassment_pattern": "Pattern analysis unavailable without Groq API key.",
            "recommended_action": "Monitor conversation." if risk_score > 40 else "No action needed."
        }

    from groq import Groq
    client = Groq(api_key=api_key)
    
    chat_text = "\n".join([f"Message {i+1}: {msg}" for i, msg in enumerate(messages)])

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
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a moderation AI that outputs strict JSON."},
                {"role": "user", "content": prompt},
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=150,
            response_format={"type": "json_object"}
        )
        import json
        content = chat_completion.choices[0].message.content.strip()
        data = json.loads(content)
        
        # Rule-based action recommendation based on computed risk score
        if risk_score >= 75:
            rec = "Immediate intervention recommended. Ban or suspend the offending participant."
        elif risk_score >= 40:
            rec = "Review closely. Issue a warning to the offending participant."
        else:
            rec = "No immediate action required. Monitor for future escalation."
            
        return {
            "overall_sentiment": data.get("overall_sentiment", "Unknown"),
            "harassment_pattern": data.get("harassment_pattern", "Unknown"),
            "recommended_action": rec
        }
    except Exception as e:
        print(f"Summarize Error: {e}")
        return {
            "overall_sentiment": "Unknown",
            "harassment_pattern": "Analysis failed.",
            "recommended_action": "Manual review required due to API error."
        }

