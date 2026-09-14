import os
import re
from groq import Groq

MODEL = "llama3-8b-8192"
MAX_FILE_TEXT_CHARS = 12000  # ~3k tokens — enough context without hitting limits


def _groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set.")
    return Groq(api_key=api_key)


def _strip_think(text: str) -> str:
    """Remove <think>...</think> reasoning blocks Qwen outputs."""
    if "<think>" in text and "</think>" not in text:
        text = text.split("<think>")[0]
    
    clean = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return clean if clean else "I'm sorry, I was interrupted while processing your request. Please try again with a shorter query."


def generate_chat_response(history: list, persona: str = "user", prediction_context: dict = None) -> str:
    """
    Generates a chatbot response using the Groq API.
    Only answers questions related to cyber crimes, digital safety,
    incident file details, and cyber news.

    Args:
        history: list of {"role": "user"|"assistant", "content": str}
        persona: "user" (empathetic/safety) or "analyst" (investigative/tactical)
        prediction_context: optional dict containing the full prediction result

    Returns:
        Markdown-formatted response string.
    """
    try:
        client = _groq_client()
    except RuntimeError as e:
        return f"System error: {e}. The cyber assistant is unavailable."

    if persona == "analyst":
        system_content = (
            "You are ShieldAI's senior cyber investigator and analyst assistant. "
            "Your role is to assist the organization in analyzing complaints based on real platform signals. "
            "You should suggest tactical next steps using only available data (fusion evidence, threat intel data, "
            "behavioral profiles, risk scores, and anomaly detection logs). "
            "Do not suggest capabilities the platform lacks, such as IP tracking or OSINT extraction. "
            "Keep your responses concise, highly tactical, and formatted in Markdown."
        )
    else:
        system_content = (
            "You are ShieldAI's cyber security assistant. You must ONLY provide information "
            "related to cyber crimes, digital safety, incident file details, and cyber news. "
            "Provide empathetic, supportive, and actionable personal safety steps. "
            "If the user asks about anything else, politely decline and remind them that you are a specialized cyber security assistant. "
        )
        
        if prediction_context:
            evidence_plan = prediction_context.get("evidence_plan", {})
            threat_intel = prediction_context.get("threat_intel", {})
            
            # Format context string
            system_content += f"""
            
You have analyzed an incident with the following details:
Current case context:
- Source: {prediction_context.get("source", "Unknown")}
- Category: {prediction_context.get("category", "Unknown")}
- Risk Score: {prediction_context.get("risk_score", "Unknown")}/100
- PII detected: {", ".join(prediction_context.get("pii_categories", [])) if prediction_context.get("pii_categories") else "No"}
- Messages flagged: {prediction_context.get("text_full", "Unknown")}
- Similar past incidents: {len(prediction_context.get("similar_reports", []))} matches
- Threat intel URLs: {len(threat_intel.get("urls", []))}
- Threat intel Emails: {len(threat_intel.get("emails", []))}

Structured Action Plan:
Case Summary: {evidence_plan.get("case_summary", "")}
Evidence to Preserve: {", ".join(evidence_plan.get("evidence_checklist", []))}
Safety Actions: {", ".join(evidence_plan.get("safety_actions", []))}

CRITICAL INSTRUCTION: You MUST structure your response into exactly these three sections, using Markdown headers:
### Detected Evidence
(Briefly summarize what was flagged based on the plan and context)
### AI Interpretation
(Assess the severity and context, explain why it's high risk if applicable)
### General Advice
(Provide empathetic advice aligned with the safety actions and next steps)

Do not output a <think> block or any reasoning process under any circumstances. Answer directly.
"""
        else:
            system_content += (
                "CRITICAL INSTRUCTION: You must keep your responses EXTREMELY short and concise. "
                "Answer in exactly one short paragraph (under 3 sentences). Do NOT use lists, bullet points, or long explanations. "
                "Do NOT output a <think> block or any reasoning process under any circumstances. Answer directly."
            )

    system_prompt = {
        "role": "system",
        "content": system_content,
    }



    formatted_messages = [system_prompt]
    for msg in history:
        role = msg.get("role")
        if role not in ["user", "assistant"]:
            continue
        formatted_messages.append({"role": role, "content": msg.get("content", "")})

    try:
        completion = client.chat.completions.create(
            messages=formatted_messages,
            model=MODEL,
            temperature=0.5,
            max_tokens=500,
        )
        return _strip_think(completion.choices[0].message.content.strip())
    except Exception as e:
        print(f"Chatbot Error: {e}")
        return "I'm sorry, I'm having trouble connecting to my neural network right now. Please try again later."


def extract_text_from_file(file_path: str, filename: str) -> str:
    """
    Extracts plain text from a variety of file formats.

    Supported: .pdf, .txt, .md, .log, .csv, .json, .docx, .py, .html, .xml
    Images (.png, .jpg, .jpeg, .webp) are handled via OCR if easyocr is available.

    Returns:
        Extracted text (may be truncated to MAX_FILE_TEXT_CHARS).
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    try:
        # ── PDF ──
        if ext == "pdf":
            import pdfplumber
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t:
                        text_parts.append(t)
            return "\n\n".join(text_parts)[:MAX_FILE_TEXT_CHARS]

        # ── Word document ──
        if ext == "docx":
            import docx
            doc = docx.Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs)[:MAX_FILE_TEXT_CHARS]

        # ── Images (OCR) ──
        if ext in {"png", "jpg", "jpeg", "webp", "bmp"}:
            try:
                import easyocr
                reader = easyocr.Reader(["en"], gpu=False)
                results = reader.readtext(file_path, detail=0)
                return " ".join(results)[:MAX_FILE_TEXT_CHARS]
            except Exception as ocr_err:
                return f"[OCR failed: {ocr_err}]"

        # ── Plain text fallback ──
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()[:MAX_FILE_TEXT_CHARS]

    except Exception as e:
        raise RuntimeError(f"Could not read file '{filename}': {e}")


def analyze_file_content(extracted_text: str, filename: str) -> str:
    """
    Calls Groq to summarize a file and recommend next steps.

    Returns:
        Markdown-formatted analysis.
    """
    try:
        client = _groq_client()
    except RuntimeError as e:
        return f"System error: {e}."

    prompt = f"""You are ShieldAI's cyber security assistant analyzing an uploaded file.

Filename: {filename}

Extracted content (may be truncated):
---
{extracted_text}
---

Please provide:
1. **File Summary** — What does this file contain? (2-4 sentences)
2. **Cyber Relevance** — Any cyber security concerns, threats, or sensitive information identified.
3. **Recommended Next Steps** — Concrete actions the user should take based on the content.

Format your entire response in clean Markdown. Be specific and practical."""

    try:
        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are ShieldAI's cyber security file analyst. "
                        "Analyze uploaded files and provide clear summaries and actionable cyber security guidance. "
                        "Always format your response in Markdown."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            model=MODEL,
            temperature=0.2,
            max_tokens=900,
        )
        return _strip_think(completion.choices[0].message.content.strip())
    except Exception as e:
        print(f"File analysis error: {e}")
        return "I was unable to analyze this file. Please try again later."
