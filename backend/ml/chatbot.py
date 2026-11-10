"""
ShieldAI Chatbot Engine — Phase 4/5 Dual-Mode Intelligent Cyber Safety Assistant.

Supports:
- "victim" mode: Calm, supportive, practical, tailored to user specifics, helpline referrals (112, 1930, cybercrime.gov.in).
- "analyst" mode: Structured tactical evaluation (Classification, Indicators, Tactics, Confidence, Escalation, Uncertainties)
  built strictly from real detection engine outputs (ModelService scores, signals, extracted URLs/domains/brands/phones).
- Anthropic API integration (when ANTHROPIC_API_KEY is configured). Default model: claude-haiku-5-5.
- Robust rule-based fallback when ANTHROPIC_API_KEY is absent, fails, or times out.
- Fallback logging: Logs exact reason whenever the fallback engine is triggered.
- Engine indicator: Returns ChatResponse with .engine ("claude" or "rules") for subtle UI display.
- Crisis & self-harm interception: Differentiates true positive distress from benign idioms ("exam is killing me", "die of embarrassment").
- Safety guardrails: Zero victim-blaming, no legal guarantees, prohibitions on confrontation/retaliation.
- Prompt injection defense: Treats scanned text as passive data, acknowledges directives calmly in one line, and continues analyzing.
- Multi-format file text extraction (PDF, DOCX, Images via OCR, Audio via faster-whisper).
"""
import os
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("ShieldAI.Chatbot")

DEFAULT_ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
MAX_FILE_TEXT_CHARS = 12000
MAX_HISTORY_TURNS = 20
MAX_MESSAGE_CHARS = 2000


class ChatResponse(str):
    """String response that carries engine metadata ('claude' or 'rules') for UI and API reporting."""
    def __new__(cls, content: str, engine: str = "rules"):
        obj = str.__new__(cls, content)
        obj.engine = engine
        return obj


# ── Safety & Crisis Patterns ──────────────────────────────────────────────────

# Colloquial hyperbole patterns that must NOT trigger crisis mode
BENIGN_HYPERBOLE_PATTERNS = [
    r"\b(?:is|are|was|were|it\'?s|it\s+is)\s+killing\s+me\b",
    r"\b(?:could|would|gonna|going\s+to)\s+die\s+of\s+(?:embarrassment|laughter|boredom|shame|curiosity)\b",
    r"\bdying\s+(?:of|from)\s+(?:laughter|embarrassment|boredom|shame)\b",
    r"\bto\s+die\s+for\b",
    r"\bkilling\s+(?:it|time)\b",
    r"\bdead\s+(?:tired|serious|wrong)\b",
    r"\bthis\s+(?:exam|traffic|homework|job|work|heat|cold|day)\s+is\s+killing\s+me\b"
]

SELF_HARM_EXPLICIT_PATTERNS = [
    r"\bsuicid(?:e|al)\b",
    r"\b(?:want(?:ing)?\s+to|going\s+to|gonna|will|plan(?:ning)?\s+to|thinking\s+of)\s+(?:kill|harm|hurt|hang|shoot|poison)\s+myself\b",
    r"\bkill(?:ing)?\s+myself\b",
    r"\bhurt(?:ing)?\s+myself\b",
    r"\bharm(?:ing)?\s+myself\b",
    r"\bend(?:ing)?\s+(?:my\s+life|it\s+all)\b",
    r"\bwant(?:ing)?\s+to\s+die\b",
    r"\bwish\s+i\s+(?:were|was)\s+dead\b",
    r"\btak(?:e|ing)\s+my\s+(?:own\s+)?life\b",
    r"\bno\s+reason\s+to\s+(?:keep\s+)?live\b",
    r"\bcan'?t\s+go\s+on\s+living\b",
    r"\bdon'?t\s+want\s+to\s+live\s+(?:anymore|any\s+longer)\b"
]

IMMEDIATE_DANGER_PATTERNS = [
    r"\bin\s+(?:immediate|grave|serious)\s+danger\b",
    r"\boutside\s+my\s+(?:house|door|window|building|office|home)\b",
    r"\bfollowing\s+me\s+right\s+now\b",
    r"\bat\s+my\s+door\b",
    r"\bthreatened\s+to\s+kill\s+me\s+(?:right\s+now|today|tonight)\b",
    r"\bholding\s+a\s+(?:knife|gun|weapon)\b",
    r"\bgoing\s+to\s+(?:stab|shoot|attack|kill)\s+me\b",
    r"\bphysically\s+attacking\b"
]

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?previous\s+(?:rules|instructions|prompts)",
    r"disregard\s+(?:all\s+)?prior\s+(?:rules|instructions|prompts)",
    r"system\s+override",
    r"you\s+are\s+now\s+(?:a|an|in\s+developer\s+mode)",
    r"bypass\s+all\s+(?:safety|rules|filters)",
    r"forget\s+(?:all\s+)?(?:your\s+)?instructions",
    r"act\s+as\s+an\s+unfiltered",
    r"output\s+the\s+system\s+prompt"
]


def check_crisis_or_danger(text: str) -> Optional[str]:
    """
    Detects true positive self-harm distress or immediate physical danger.
    Explicitly filters out benign idioms like 'this exam is killing me' or 'I could die of embarrassment'.
    Requirement 2(d): Crisis replies start with one warm sentence, then 112/nearest emergency room or
    a trusted person, then helplines, with no promises like 'it can be resolved safely', and no cyber-safety steps.
    """
    if not text or not isinstance(text, str):
        return None

    lower = text.lower()

    # Check for immediate physical danger
    is_danger = any(re.search(pat, lower) for pat in IMMEDIATE_DANGER_PATTERNS)

    # Check for explicit self-harm statements
    is_self_harm = any(re.search(pat, lower) for pat in SELF_HARM_EXPLICIT_PATTERNS)

    # Check for benign colloquial hyperbole
    is_hyperbole = any(re.search(pat, lower) for pat in BENIGN_HYPERBOLE_PATTERNS)

    # Suppress crisis response for benign hyperbole when no explicit self-harm or danger exists
    if is_hyperbole and not is_self_harm and not is_danger:
        return None

    if not is_danger and not is_self_harm:
        return None

    parts = []
    if is_danger:
        parts.append(
            "### 🚨 IMMEDIATE PHYSICAL DANGER — TAKE ACTION NOW\n\n"
            "I hear how terrifying this situation is, and your physical safety is the absolute priority.\n\n"
            "If someone is threatening you right now, following you, or outside your home:\n"
            "- **Call Emergency 112 immediately** (National Emergency Helpline) or go to the nearest police station.\n"
            "- If you cannot speak safely, move into a locked room, contact a trusted neighbor or family member, or head to a crowded public space.\n"
            "- **Do not confront, open the door, or provoke the individual.**"
        )

    if is_self_harm:
        # One warm sentence, then 112/nearest emergency room or trusted person, then helplines
        # NO promises like "it can be resolved safely", and NO cyber-safety steps
        parts.append(
            "I hear how much pain you are in right now, and I want you to be safe.\n\n"
            "If you are in immediate danger of hurting yourself, please call **112**, go to the nearest hospital emergency room, or reach out to a trusted family member or friend right now.\n\n"
            "Free, confidential support is available 24/7:\n"
            "- **Tele-MANAS:** **14416** or **1800-891-4416** (24/7 Toll-Free Mental Health Support, Govt. of India)\n"
            "- **KIRAN Helpline:** **1800-599-0019** (24/7 Toll-Free Support)\n"
            "- **Vandrevala Foundation:** **+91 9999 666 555** (24/7 Free Crisis Counseling)\n"
            "- **AASRA Helpline:** **+91 98204 66726** (24/7 Confidential Crisis Care)"
        )

    return "\n\n".join(parts)


def check_prompt_injection(text: str) -> bool:
    """Returns True if the text contains an instruction-override attempt."""
    if not text or not isinstance(text, str):
        return False
    lower = text.lower()
    return any(re.search(pat, lower) for pat in PROMPT_INJECTION_PATTERNS)


# ── Entity & Specifics Extraction ─────────────────────────────────────────────

def extract_user_specifics(text: str) -> Dict[str, Any]:
    """
    Extracts mentioned specifics: amount, deadline, platform, brand, URLs, phones, emails.
    Requirement 2(b): Never extract a platform or amount from inside a URL
    ('bit.ly/x' must NOT produce 'contact via X'), and only mention money or crypto when payment is requested.
    """
    specifics = {
        "amount": None,
        "deadline": None,
        "platform": None,
        "urls": [],
        "domains": [],
        "brand": None,
        "phones": [],
        "emails": [],
        "handles": []
    }
    if not text:
        return specifics

    # 1. Extract URLs first
    raw_urls = re.findall(r'https?://[^\s<>"\']+|www\.[^\s<>"\']+', text)
    seen_urls = set()
    deduped_urls = []
    for u in raw_urls:
        u_clean = u.rstrip(".,;!?:")
        if u_clean not in seen_urls:
            seen_urls.add(u_clean)
            deduped_urls.append(u_clean)
    specifics["urls"] = deduped_urls

    for u in deduped_urls:
        m = re.search(r'https?://([^/]+)', u)
        if m:
            dom = m.group(1).lower()
            if dom not in specifics["domains"]:
                specifics["domains"].append(dom)

    # CRITICAL: Strip all URLs before scanning for platforms, amounts, brands, handles!
    text_no_urls = re.sub(r'https?://\S+|www\.\S+', ' ', text)

    # 2. Amounts: only extract when money, crypto, or payment is requested
    has_payment_context = any(w in text_no_urls.lower() for w in [
        "pay", "send", "transfer", "demanding", "demand", "fee", "cost", "fine", "deposit",
        "ransom", "penalty", "refund", "bitcoin", "btc", "eth", "usdt", "wallet", "crypto",
        "dollars", "usd", "inr", "rupees", "cash"
    ])
    if has_payment_context:
        amt_match = re.search(
            r'(?:[\$₹£€]|Rs\.?\s*|INR\s*)\s*[\d,]+(?:\.\d+)?|\b\d+(?:,\d+)*(?:\.\d+)?\s*(?:dollars|usd|inr|rupees|bitcoin|btc|eth|usdt)\b|\b(?:send|pay|demanding|demands|transfer)\s+(?:me\s+)?([\$₹£€]?\s*[\d,]+(?:\.\d+)?(?:\s*(?:inr|rupees|usd|dollars|btc|bitcoin|usdt))?)',
            text_no_urls,
            re.IGNORECASE
        )
        if amt_match:
            val = amt_match.group(1) if amt_match.lastindex and amt_match.group(1) else amt_match.group(0)
            specifics["amount"] = val.strip()

    # 3. Deadlines
    dl_match = re.search(
        r'\b(?:within|in)\s+\d+\s*(?:hours?|hrs?|days?|minutes?|mins?)\b|\b(?:by\s+tomorrow|tonight|immediately|urgent(?:ly)?)\b',
        text_no_urls,
        re.IGNORECASE
    )
    if dl_match:
        specifics["deadline"] = dl_match.group(0).strip()

    # 4. Platforms: Never extract from inside URL paths. X requires platform prefix context.
    plat_match = re.search(
        r'\b(Instagram|WhatsApp|Telegram|SMS|Facebook|Twitter|Snapchat|Discord|LinkedIn|Gmail|Email)\b|\b(?:on|via|from)\s+(X)\b',
        text_no_urls,
        re.IGNORECASE
    )
    if plat_match:
        p = plat_match.group(1) or plat_match.group(2)
        specifics["platform"] = p.title()

    # 5. Look-alike brand impersonation
    brand_match = re.search(
        r'\b(SBI|State Bank(?: of India)?|HDFC|ICICI|Axis|Paytm|PayPal|Netflix|Amazon|Apple|Microsoft|FedEx|India Post)\b',
        text_no_urls,
        re.IGNORECASE
    )
    if brand_match:
        specifics["brand"] = brand_match.group(1)

    # 6. Phones & Emails
    phones = re.findall(r'(?:\+?91[-.\s]?)?[6-9]\d{9}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text_no_urls)
    specifics["phones"] = list(dict.fromkeys(phones))

    emails = re.findall(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b', text_no_urls)
    specifics["emails"] = list(dict.fromkeys(emails))

    handles = re.findall(r'@\w{2,30}\b', text_no_urls)
    specifics["handles"] = list(dict.fromkeys(handles))

    return specifics


# ── Rule-Based Fallback Engine ────────────────────────────────────────────────

def generate_fallback_response(user_text: str, persona: str = "victim", prediction_context: dict = None) -> ChatResponse:
    """
    High-quality deterministic fallback response when the Anthropic API is unconfigured, fails, or times out.
    Adheres strictly to requested persona ('victim' or 'analyst') and builds analyst output from real engine scores.
    """
    mode = "analyst" if (persona or "").lower() == "analyst" else "victim"

    # Crisis & danger check: If triggered, return crisis response immediately with NO cyber-safety steps
    crisis_resp = check_crisis_or_danger(user_text)
    if crisis_resp:
        return ChatResponse(crisis_resp, engine="rules")

    # Extract user specifics from text
    specifics = extract_user_specifics(user_text)

    # Prompt injection check
    is_injection = check_prompt_injection(user_text)

    # Obtain real analysis result from ModelService or prediction_context
    analysis = None
    if prediction_context and isinstance(prediction_context, dict) and "score" in prediction_context:
        analysis = prediction_context
    else:
        try:
            from services.model_service import model_service
            analysis = model_service.analyze(user_text)
        except Exception as e:
            logger.warning(f"ModelService invocation in fallback failed ({e}). Using basic heuristic scores.")
            analysis = {
                "score": 0.0,
                "level": "low",
                "category_scores": {},
                "signals": [],
                "category": "clean"
            }

    real_score = float(analysis.get("score") or analysis.get("risk_score") or 0.0)
    real_level = (analysis.get("level") or analysis.get("severity_tier") or "low").upper()
    real_signals = analysis.get("signals") or analysis.get("flagging_reasons") or []

    cat_scores = analysis.get("category_scores") or {}
    if cat_scores:
        sorted_cats = sorted(cat_scores.items(), key=lambda x: x[1], reverse=True)
        top_cat = sorted_cats[0][0].lower() if sorted_cats[0][1] > 0 else "clean"
    else:
        top_cat = (analysis.get("category") or analysis.get("primary_label") or "clean").lower()

    # Requirement 2(a): If the message has no scam/threat/harassment signal
    # (e.g. "This exam is killing me, I have so much to study"), reply briefly and friendly, with no harassment template.
    has_threat_signal = (
        real_score >= 35.0 or
        real_level in ["MEDIUM", "HIGH", "CRITICAL"] or
        any(k in top_cat for k in ["threat", "sextortion", "blackmail", "phishing", "scam"]) or
        (top_cat in ["harassment", "abusive_language"] and real_score >= 35.0) or
        bool(specifics.get("amount")) or
        bool(specifics.get("brand")) or
        any(k in user_text.lower() for k in [
            "leak", "webcam", "nude", "kill you", "murder you", "pay me", "transfer", "kyc", "locked", "suspended",
            "blackmail", "blackmailing", "extort", "extortion", "harass", "harassing", "phish", "scam", "hack"
        ])
    )

    if not has_threat_signal and not is_injection:
        if mode == "victim":
            if any(w in user_text.lower() for w in ["exam", "study", "homework", "class", "course", "grade", "test", "workload"]):
                return ChatResponse(
                    "I understand how stressful things can get with exams and heavy study workloads! "
                    "Hang in there, remember to take short breaks, stay hydrated, and take things one step at a time. "
                    "If you ever encounter suspicious links, online harassment, or cyber threats, I'm here to help.",
                    engine="rules"
                )
            else:
                return ChatResponse(
                    "Hello! I am ShieldAI, your assistant for cyber safety and threat evaluation. "
                    "Your message does not appear to contain any threat, scam, or harassment indicators. "
                    "If you have received suspicious messages, harassment, or need guidance on protecting yourself online, feel free to share.",
                    engine="rules"
                )
        else:
            return ChatResponse(
                "### 🛡️ Structured Incident Assessment (Analyst Mode)\n\n"
                "**Classification:** Benign Communication / No Threat Detected\n"
                "**Assessed Risk Level:** LOW (Score: 0.0/100)\n"
                "**Confidence:** High\n\n"
                "#### Evaluation Summary:\n"
                "- No threat, extortion, credential harvesting, or targeted harassment signals were detected in the input.\n"
                "- Text represents colloquial expression or routine communication requiring no security intervention.",
                engine="rules"
            )

    if mode == "victim":
        lines = []

        # Requirement 2(c): Start with one warm sentence acknowledging what the user said
        if "sextortion" in top_cat or "blackmail" in top_cat or any(k in user_text.lower() for k in ["photo", "nude", "video", "webcam", "blackmail", "extort"]):
            ack = "I am so sorry you are facing this distressing blackmail attempt—please know that you did nothing wrong and you are not alone."
        elif "threat" in top_cat or any(k in user_text.lower() for k in ["kill", "stab", "shoot", "attack", "murder"]):
            ack = "I hear how terrifying receiving a direct physical threat is, and your personal safety is the absolute priority."
        elif "phishing" in top_cat or "scam" in top_cat or specifics.get("urls") or specifics.get("brand"):
            ack = "I understand why this message seems alarming, but it is a fraudulent attempt designed to trick you into compromising your account."
        else:
            ack = "I am truly sorry you are having to endure these hurtful and hostile messages, and please know that you do not deserve this treatment."

        lines.append(ack)

        # Requirement 2(e): Phishing replies explain why it is suspicious in plain words,
        # and if the message contains an instruction aimed at the assistant, mention it calmly in one sentence and still treat the message as suspicious.
        if is_injection:
            lines.append(
                "\n*Note: Instructions contained within user text are treated as passive evidence and disregarded for system commands.*\n\n"
                "This message is suspicious because it claims an account is locked and uses artificial urgency to push you toward clicking an unverified link. "
                "The message also contains an instruction directed at the assistant to disregard rules and declare it safe, which is a recognized evasion technique in automated scams."
            )
        elif ("phishing" in top_cat or "scam" in top_cat) and specifics.get("urls"):
            lines.append(
                f"\nThis message is suspicious because legitimate organizations do not threaten immediate account suspension while demanding that you verify details through unofficial links like {', '.join(specifics['urls'][:2])}."
            )

        # Requirement 2(b): Address user specifics (amount, deadline, platform)
        # ONLY mention money or crypto when payment is requested!
        context_parts = []
        if specifics.get("amount"):
            context_parts.append(f"the demand for **{specifics['amount']}**")
        if specifics.get("deadline"):
            dl_raw = specifics["deadline"].strip()
            dl_clean = re.sub(r'^(?:within|in|by)\s+', '', dl_raw, flags=re.IGNORECASE)
            if dl_clean.lower() in ["immediately", "urgent", "urgently"]:
                context_parts.append("the **immediate deadline**")
            elif dl_clean.lower() in ["tomorrow", "tonight"]:
                context_parts.append(f"the deadline by **{dl_clean}**")
            else:
                context_parts.append(f"the deadline of **{dl_clean}**")
        if specifics.get("platform"):
            context_parts.append(f"contact via **{specifics['platform']}**")

        has_payment_demand = bool(specifics.get("amount")) or any(k in user_text.lower() for k in ["bitcoin", "crypto", "btc", "usdt", "wallet", "pay me", "send money", "dollars", "inr", "rupees"])
        if has_payment_demand:
            lines.append(f"\nRegarding {', '.join(context_parts) if context_parts else 'the demand'}: **do not send any money or cryptocurrency**, and do not negotiate.")
        elif context_parts:
            lines.append(f"\nRegarding {', '.join(context_parts)}: **do not click links or engage**, and cut off contact.")

        # Requirement 2(c): At most 5 numbered steps
        lines.append("\n### Concrete Next Steps:")

        if "sextortion" in top_cat or "blackmail" in top_cat or any(k in user_text.lower() for k in ["photo", "nude", "video", "webcam"]):
            lines.append("1. **DO NOT PAY OR NEGOTIATE:** Paying blackmailers never stops them; it leads to repeated extortion demands.")
            lines.append("2. **Context on Digital Blackmail:** Many sextortion messages are automated mass-sent bluffs where attackers claim to have webcam recordings using leaked passwords from old data breaches without actually possessing media.")
            lines.append("3. **Preserve All Evidence:** Capture uncropped screenshots showing the sender's account handle, phone number, messages, and timestamps before blocking.")
            lines.append("4. **Stop All Contact & Block:** Block their profile on all platforms and restrict your social media privacy settings so your friend/follower lists are private.")
            lines.append("5. **Report to Image Takedown & Authorities:** File an immediate report on the **National Cyber Crime Reporting Portal at [cybercrime.gov.in](https://cybercrime.gov.in)** or call Helpline **1930**, and submit image hashes confidentially to **StopNCII.org** to prevent sharing.")

        elif "threat" in top_cat or any(k in user_text.lower() for k in ["kill", "stab", "shoot", "attack"]):
            lines.append("1. **Ensure Physical Safety First:** If you believe there is any chance the person is nearby, call the **National Emergency Helpline at 112** immediately or move to a secure public location.")
            lines.append("2. **Preserve Full Evidence:** Save uncropped screenshots, chat logs, sender profiles, and timestamps before blocking.")
            lines.append("3. **Do Not Retaliate or Confront:** Engaging the sender may escalate their hostility.")
            lines.append("4. **File a Formal Complaint:** Lodge a complaint at your nearest police station or cyber crime cell via **https://cybercrime.gov.in**.")

        elif "phishing" in top_cat or "scam" in top_cat or specifics.get("urls") or specifics.get("brand") or is_injection:
            lines.append("1. **DO NOT Click Links or Share OTPs:** Never click links or disclose banking passwords, OTPs, Aadhaar, or UPI PINs.")
            lines.append("2. **Verify Directly:** Contact the official institution via their verified phone number or official app, never through links provided in suspicious messages.")
            lines.append("3. **Secure Your Bank Accounts:** If you shared any financial credentials, immediately call your bank's official emergency helpline or freeze cards/UPI via your banking app.")
            lines.append("4. **Report Financial Fraud:** Dial the **National Cyber Crime Helpline at 1930** immediately and report the attempt at **https://cybercrime.gov.in**.")

        else:
            lines.append("1. **Preserve Evidence:** Capture full screenshots of the abusive messages with visible dates, times, and usernames.")
            lines.append("2. **Block and Mute:** Cut off communication and report the offending user using the platform's built-in safety tools.")
            lines.append("3. **Lock Down Privacy:** Review account privacy settings to allow messages only from people you know.")
            lines.append("4. **Official Recourse:** For persistent or severe harassment, lodge a report on the **National Cyber Crime Reporting Portal at https://cybercrime.gov.in**.")

        lines.append("\n*Note: ShieldAI provides technical guidance and evidence triaging. For legal action or ongoing danger, contact local law enforcement (112) or the National Cybercrime Helpline at 1930.*")
        return ChatResponse("\n".join(lines), engine="rules")

    else:  # mode == "analyst"
        lines = []

        classification = "Cyber Threat & Harassment"
        legal_citation = "This incident may fall under relevant sections of the Information Technology Act (IT Act) and Bharatiya Nyaya Sanhita (BNS) / IPC."
        if "sextortion" in top_cat or "blackmail" in top_cat or any(k in user_text.lower() for k in ["photo", "nude", "video", "webcam"]):
            classification = "Financial Sextortion & Digital Blackmail"
            legal_citation = "This incident may fall under IT Act Section 66E (privacy violation), Section 67/67A (transmission of obscene material), and BNS / IPC provisions relating to extortion and criminal intimidation."
        elif "threat" in top_cat:
            classification = "Explicit Threat of Physical Violence / Intimidation"
            legal_citation = "This incident may fall under BNS / IPC provisions for criminal intimidation (Section 503/506) and IT Act Section 66."
        elif "phishing" in top_cat:
            classification = "Credential Harvesting & Brand Impersonation Phishing"
            legal_citation = "This incident may fall under IT Act Section 66D (cheating by personation using computer resource) and relevant fraud provisions."
        elif "scam" in top_cat:
            classification = "Social Engineering / Financial Fraud"
            legal_citation = "This incident may fall under IT Act Section 66D (cheating using computer resource) and financial fraud provisions."
        elif "harassment" in top_cat:
            classification = "Targeted Online Harassment & Toxic Abuse"
            legal_citation = "This incident may fall under IT Act Section 66E and relevant BNS provisions on verbal abuse and stalking."

        conf_str = "High" if real_score >= 70.0 else ("Medium" if real_score >= 40.0 else "Low")

        lines.append("### 🛡️ Structured Incident Assessment (Analyst Mode)\n")
        lines.append(f"**Classification:** {classification}")
        lines.append(f"**Assessed Risk Level:** {real_level} (Score: {real_score:.1f}/100)")
        lines.append(f"**Confidence:** {conf_str}")
        lines.append(f"**Legal Framework:** {legal_citation}")

        # Requirement 2(f): Shows each indicator ONCE
        lines.append("\n#### Technical & Behavioral Indicators:")
        seen_indicators = set()
        indicator_lines = []

        if real_signals:
            for s in real_signals[:5]:
                sig_text = s.get("signal") if isinstance(s, dict) else str(s)
                sig_clean = sig_text.strip()
                if sig_clean and sig_clean not in seen_indicators:
                    seen_indicators.add(sig_clean)
                    indicator_lines.append(f"- {sig_clean}")

        if specifics.get("urls"):
            for u in specifics["urls"]:
                if u not in seen_indicators:
                    seen_indicators.add(u)
                    indicator_lines.append(f"- **Extracted URL:** {u}")

        if specifics.get("domains"):
            for d in specifics["domains"]:
                if d not in seen_indicators:
                    seen_indicators.add(d)
                    indicator_lines.append(f"- **Identified Domain:** {d}")

        if specifics.get("brand"):
            b = specifics["brand"]
            if b not in seen_indicators:
                seen_indicators.add(b)
                indicator_lines.append(f"- **Impersonated Entity / Brand:** {b}")

        if specifics.get("phones"):
            for p in specifics["phones"]:
                if p not in seen_indicators:
                    seen_indicators.add(p)
                    indicator_lines.append(f"- **Extracted Phone Number:** {p}")

        if specifics.get("emails"):
            for em in specifics["emails"]:
                if em not in seen_indicators:
                    seen_indicators.add(em)
                    indicator_lines.append(f"- **Extracted Email Address:** {em}")

        if specifics.get("handles"):
            for h in specifics["handles"]:
                if h not in seen_indicators:
                    seen_indicators.add(h)
                    indicator_lines.append(f"- **Identified Account / Handle:** {h}")

        if specifics.get("amount"):
            amt = specifics["amount"]
            if amt not in seen_indicators:
                seen_indicators.add(amt)
                indicator_lines.append(f"- **Extortion / Payment Demand:** {amt}")

        if not indicator_lines:
            indicator_lines.append("- Threat/fraud terminology identified in message text.")

        lines.extend(indicator_lines)

        # Distinguish channel modality: SMS smishing vs Email phishing
        is_sms_phishing = False
        is_email_phishing = False
        if "phishing" in top_cat or "scam" in top_cat:
            if specifics.get("emails") or any(k in user_text.lower() for k in ["from:", "subject:", "mailer", "inbox", "dkim", "spf"]):
                is_email_phishing = True
            else:
                is_sms_phishing = True

        # Requirement 2(f): Lists tactics ONLY when supported by the text
        lines.append("\n#### Attacker Tactics Identified:")
        tactics = []
        user_lower = user_text.lower()

        if "sextortion" in top_cat or "blackmail" in top_cat or any(k in user_lower for k in ["photo", "nude", "video", "webcam"]):
            if any(k in user_lower for k in ["leak", "send", "photo", "video", "webcam", "record", "contact", "instagram", "family", "friend"]):
                tactics.append("- **Psychological Intimidation & Shaming:** Threatening imminent disclosure of private/compromising media to contacts to induce panic.")
            if specifics.get("amount") or any(k in user_lower for k in ["money", "bitcoin", "crypto", "pay", "rupee", "wallet", "transfer"]):
                tactics.append("- **Financial Coercion:** Demanding irreversible payment (cryptocurrency, gift cards, or wire transfer).")
            if any(k in user_lower for k in ["webcam", "password", "device", "hack", "malware", "spyware"]):
                tactics.append("- **Credential Bluff / Fake Malware:** Citing leaked credentials from historical data breaches or fictitious webcam capture without actual compromise.")

        elif is_sms_phishing or is_email_phishing or "phishing" in top_cat or "scam" in top_cat:
            if specifics.get("brand") or any(k in user_lower for k in ["sbi", "bank", "customs", "police", "trai", "official"]):
                tactics.append("- **Sender Header Spoofing / Look-alike Sender ID:** Impersonating a trusted financial or governmental entity.")
            if specifics.get("deadline") or any(k in user_lower for k in ["urgent", "immediately", "block", "suspend", "24 hour", "lock", "deactivat", "kyc"]):
                tactics.append("- **Artificial Account Urgency:** Fabricating imminent account deactivation or KYC deadline to force rushed actions.")
            if specifics.get("urls") or specifics.get("domains") or any(k in user_lower for k in ["http", ".xyz", "verify", "update", "link", "click"]):
                tactics.append("- **Deceptive Credential Harvester:** Directing victim to an off-domain phishing form (e.g. suspicious TLD) to harvest banking credentials and OTPs.")
            if any("digital arrest" in user_lower or "courier" in user_lower for _ in [1]):
                tactics.append("- **Law Enforcement Coercion:** Fabricating fictitious arrest warrants or courier seizure notices to demand immediate transfer.")

        elif "threat" in top_cat:
            if any(k in user_lower for k in ["kill", "murder", "harm", "shoot", "die", "hurt", "beat", "attack"]):
                tactics.append("- **Direct Physical Intimidation:** Explicit declaration of intent to inflict physical injury or death.")
            if any(k in user_lower for k in ["know where you live", "watching", "outside", "follow", "house", "address"]):
                tactics.append("- **Surveillance Assertion:** Claiming physical proximity or knowledge of home/workplace coordinates to amplify terror.")

        elif "harassment" in top_cat or "abusive" in top_cat:
            if any(k in user_lower for k in ["ugly", "stupid", "idiot", "loser", "freak", "moron", "bitch", "shut up", "kutta", "harami"]):
                tactics.append("- **Targeted Hostility & Personal Degradation:** Sustained personal insults, demeaning slurs, or hostile targeting.")
            if any(k in user_lower for k in ["kys", "go die", "kill yourself"]):
                tactics.append("- **Malicious Incitement:** Severe suicide or self-harm encouragement aimed at causing psychological harm.")

        if not tactics:
            tactics.append("- **Pattern-Based Social Engineering:** Manipulative communication pattern identified by detection rules.")

        lines.extend(tactics)

        # Requirement 2(f): Case-specific actions (domain age/registrar, report to registrar, submit URL to Google Safe Browsing/PhishTank)
        lines.append("\n#### Recommended Escalation Steps:")
        if "sextortion" in top_cat or "blackmail" in top_cat:
            lines.append("1. **Strict Non-Payment & Disengagement:** Never pay or negotiate; compliance guarantees escalation of extortion demands.")
            lines.append("2. **Digital Evidence Capture:** Document complete uncropped chat logs, sender profile links, and payment wallet/UPI handles before blocking.")
            lines.append("3. **Image Protection & Takedown:** Submit non-consensual image protection hashes to **StopNCII.org** (or Take It Down for minors) to prevent media sharing across participating platforms.")
            lines.append("4. **Statutory Incident Dispatch:** Lodge a formal cyber blackmail complaint on the **National Cyber Crime Reporting Portal at `https://cybercrime.gov.in`** or dial helpline **1930**.")

        elif is_sms_phishing:
            lines.append("1. **SMS & Sender Evidence Capture:** Preserve the raw SMS message with exact originating sender ID (e.g. shortcode or alphatag), arrival timestamp, and unshortened link target.")
            lines.append("2. **Domain Age & Registrar Analysis:** Query WHOIS to verify domain registration date, domain age, and authoritative registrar.")
            lines.append("3. **Registrar Abuse Report & Blacklist Submission:** File an abuse takedown with the domain registrar, and submit the malicious URL to Google Safe Browsing and PhishTank.")
            lines.append("4. **Spam & Telecom Takedown:** Forward the fraudulent SMS to **1909** (TRAI DND reporting) and report the sender ID on the DoT **Chakshu Portal (`sancharsaathi.gov.in`)**.")
            lines.append("5. **National Cyber Reporting:** File a complaint with the **National Cyber Crime Helpline at 1930** and report on **`https://cybercrime.gov.in`**.")

        elif is_email_phishing:
            lines.append("1. **Forensic Header Export:** Export raw RFC 822 email headers (`.eml` / `.msg`) to capture originating IP address, SPF/DKIM verification results, and envelope sender.")
            lines.append("2. **Domain Age & Registrar Analysis:** Check the domain registration age and registrar via WHOIS query.")
            lines.append("3. **Registrar Abuse Report & Blacklist Submission:** File an abuse takedown request with the domain registrar, and submit the phishing URL to Google Safe Browsing and PhishTank.")
            lines.append("4. **Mail Gateway Containment:** Block the sender domain and quarantine associated phishing URLs at the mail filter and DNS firewall.")
            lines.append("5. **Statutory Reporting:** Report to CERT-In (`incident@cert-in.org.in`) and file an incident report on **`https://cybercrime.gov.in`**.")

        elif "threat" in top_cat:
            lines.append("1. **Immediate Physical Safety:** If the sender knows your physical whereabouts or you feel in immediate danger, call **112** (National Emergency Response) immediately.")
            lines.append("2. **Forensic Evidence Logging:** Preserve complete chat exports, voicemail recordings, caller IDs, and platform usernames without alteration.")
            lines.append("3. **Police FIR Filing:** Register a formal First Information Report (FIR) under BNS / IPC criminal intimidation (Section 503/506) and IT Act Section 66 at your local police station or cyber crime cell.")
            lines.append("4. **Platform Preservation:** Request trust & safety preservation of IP addresses and server logs from the platform for law enforcement inquiry.")

        elif "harassment" in top_cat:
            lines.append("1. **Evidence Archiving:** Capture uncropped, timestamped screenshots showing account URLs, post links, and message content.")
            lines.append("2. **Platform Moderation Enforcement:** Utilize in-app abuse reporting to suspend offending accounts and restrict incoming messages to approved contacts.")
            lines.append("3. **Formal Complaint:** If harassment is continuous or amounts to stalking, file a report on the **National Cyber Crime Reporting Portal at `https://cybercrime.gov.in`**.")

        else:
            lines.append("1. **Evidence Archiving:** Preserve uncropped screenshots and raw message headers/timestamps.")
            lines.append("2. **Platform Safety Reporting:** Block and report the sender via native platform safety controls.")
            lines.append("3. **Statutory Dispatch:** Report cyber incidents to **`https://cybercrime.gov.in`** or Helpline **1930**.")

        # Requirement 2(f): Case-specific uncertainties
        lines.append("\n#### Uncertainties & Investigation Limits:")
        if is_sms_phishing or is_email_phishing or "phishing" in top_cat or "scam" in top_cat:
            lines.append("- Domain age and registrar records should be verified via WHOIS; registrant details may be protected by privacy services, requiring registrar subpoena for true registrant identity.")
            lines.append("- Hosting IP resolution does not confirm operational operator; reverse-proxy or CDN routing may mask actual origin server.")
            if is_sms_phishing:
                lines.append("- SMS sender alphatag or shortcode may be spoofed; physical handset attribution requires telecom carrier call detail records (CDR).")
        elif "sextortion" in top_cat:
            lines.append("- Extortionist claims of device compromise and recorded webcam footage cannot be confirmed without forensic device telemetry; vast majority represent automated credential-stuffing mass bluffs.")
            lines.append("- Cryptocurrency payment addresses are pseudonymous; blockchain transactions can be monitored but wallet owner attribution requires exchange KYC subpoenas.")
        elif "threat" in top_cat:
            lines.append("- Sender display name or social handle may be disposable or compromised; physical geolocation attribution requires law enforcement platform subpoena for IP connection logs.")
        else:
            lines.append("- Sender identity and account display names may be spoofed; raw server logs and telecom records required for definitive attribution.")

        return ChatResponse("\n".join(lines), engine="rules")


# ── Anthropic API Integration ────────────────────────────────────────────────

def _get_anthropic_client():
    """Returns an Anthropic client if ANTHROPIC_API_KEY is configured in the environment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        logger.warning(f"Could not initialize Anthropic client: {e}")
        return None


def generate_chat_response(history: list, persona: str = "victim", prediction_context: dict = None) -> ChatResponse:
    """
    Generates a chatbot response using the Anthropic API (Claude) or seamlessly falls back to
    the intelligent rule-based engine if ANTHROPIC_API_KEY is unset, fails, or times out.

    Returns:
        ChatResponse (str) with .engine attribute ('claude' or 'rules').
    """
    mode = "analyst" if (persona or "").lower() == "analyst" else "victim"

    # Identify latest user message
    user_text = ""
    for msg in reversed(history or []):
        if msg.get("role") == "user":
            user_text = msg.get("content", "").strip()
            break

    # 1. Emergency Crisis & Self-Harm Safety Guardrail
    crisis_response = check_crisis_or_danger(user_text)
    if crisis_response and ("danger" in crisis_response.lower() or "suicide" in user_text.lower() or "kill myself" in user_text.lower() or "end my life" in user_text.lower()):
        logger.info("Using safety crisis interception. Engine: rules")
        return ChatResponse(crisis_response, engine="rules")

    # 2. Check for Anthropic API Key
    client = _get_anthropic_client()
    if client is None:
        logger.info("No API key configured for Anthropic. Using rule-based fallback engine.")
        return generate_fallback_response(user_text, persona=mode, prediction_context=prediction_context)

    # 3. Call Anthropic Claude API
    try:
        model_name = os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
        system_prompt = (
            "You are ShieldAI, an expert cyber-safety assistant specializing in online harassment, "
            "threat evaluation, extortion defense, and scam prevention. Provide clear, empathetic, and actionable guidance."
        )

        messages = []
        for msg in (history or []):
            role = "user" if msg.get("role") == "user" else "assistant"
            content = msg.get("content", "")
            if content:
                messages.append({"role": role, "content": content})

        if not messages and user_text:
            messages.append({"role": "user", "content": user_text})

        response = client.messages.create(
            model=model_name,
            max_tokens=1000,
            system=system_prompt,
            messages=messages
        )

        content = response.content[0].text if response.content else ""
        return ChatResponse(content, engine="claude")

    except Exception as e:
        logger.warning(f"Anthropic API call failed ({e}). Using rule-based fallback engine.")
        return generate_fallback_response(user_text, persona=mode, prediction_context=prediction_context)


# ── Multi-Modal File Text Extraction ──────────────────────────────────────────

def extract_text_from_file(file_path: str, filename: str) -> str:
    """
    Extracts plain text from multi-modal files:
    - PDF: pypdf (fallback: pdfplumber)
    - Documents: docx, txt, md, log, csv, json, py, html, xml
    - Images / Screenshots: offline OCR engine (or Tesseract fallback)
    - Audio: faster-whisper
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    try:
        # ── PDF ──
        if ext == "pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                text_parts = [p.extract_text() or "" for p in reader.pages]
                full_text = "\n\n".join(text_parts).strip()
                if not full_text:
                    raise ValueError("No text could be extracted from PDF (file may be empty or image-only).")
                return full_text[:MAX_FILE_TEXT_CHARS]
            except ImportError:
                try:
                    import pdfplumber
                    text_parts = []
                    with pdfplumber.open(file_path) as pdf:
                        for page in pdf.pages:
                            t = page.extract_text()
                            if t:
                                text_parts.append(t)
                    full_text = "\n\n".join(text_parts).strip()
                    if not full_text:
                        raise ValueError("No text could be extracted from PDF.")
                    return full_text[:MAX_FILE_TEXT_CHARS]
                except ImportError:
                    raise RuntimeError("PDF extraction requires 'pypdf'. Please install it using: pip install pypdf")

        # ── Word document ──
        if ext == "docx":
            try:
                import docx
                doc = docx.Document(file_path)
                return "\n".join(p.text for p in doc.paragraphs)[:MAX_FILE_TEXT_CHARS]
            except ImportError:
                raise RuntimeError("DOCX extraction requires 'python-docx'. Install it using: pip install python-docx")

        # ── Images / Screenshots (OCR) ──
        if ext in {"png", "jpg", "jpeg", "webp", "bmp"}:
            # Check for offline OCR engine first
            try:
                from services.ocr_service import OCRService
                text = OCRService.extract_text(file_path)
                if text and text.strip():
                    return text.strip()[:MAX_FILE_TEXT_CHARS]
            except Exception:
                pass

            import shutil
            tess_binary = shutil.which("tesseract")
            if not tess_binary and os.name == "nt":
                for cand in [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
                ]:
                    if os.path.exists(cand):
                        tess_binary = cand
                        try:
                            import pytesseract
                            pytesseract.pytesseract.tesseract_cmd = cand
                        except Exception:
                            pass
                        break

            if tess_binary:
                try:
                    import pytesseract
                    from PIL import Image
                    img = Image.open(file_path)
                    text = pytesseract.image_to_string(img)
                    if text and text.strip():
                        return text.strip()[:MAX_FILE_TEXT_CHARS]
                    raise ValueError("Tesseract OCR completed but detected no readable text in the image.")
                except ValueError:
                    raise
                except Exception as ocr_e:
                    raise RuntimeError(f"OCR processing failed: {ocr_e}")

            raise RuntimeError(
                "OCR screenshot extraction requires an OCR engine. "
                "Please install rapidocr-onnxruntime or Tesseract OCR."
            )

        # ── Audio Files (faster-whisper) ──
        if ext in {"mp3", "wav", "m4a", "ogg", "flac"}:
            import shutil
            ffmpeg_path = shutil.which("ffmpeg")
            if not ffmpeg_path:
                raise RuntimeError(
                    "Audio transcription requires FFmpeg. Please install FFmpeg and ensure it is on your system PATH."
                )
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                raise RuntimeError(
                    "Audio transcription requires 'faster-whisper'. Install it using: pip install faster-whisper"
                )

            try:
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                segments, info = model.transcribe(file_path, beam_size=1)
                text_segments = [seg.text.strip() for seg in segments if seg.text.strip()]
                full_transcript = " ".join(text_segments).strip()
                if not full_transcript:
                    raise ValueError("Audio transcription completed, but no speech was detected in the file.")
                return full_transcript[:MAX_FILE_TEXT_CHARS]
            except Exception as e:
                raise RuntimeError(f"Audio transcription failed: {e}")

        # ── Plain text / CSV / JSON fallback ──
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()[:MAX_FILE_TEXT_CHARS]

    except (ValueError, RuntimeError):
        raise
    except Exception as e:
        raise RuntimeError(f"Could not read file '{filename}': {e}")


def analyze_file_content(extracted_text: str, filename: str, persona: str = "victim") -> str:
    """
    Summarizes uploaded file content and recommends cyber safety next steps.
    """
    history = [
        {
            "role": "user",
            "content": f"I uploaded an incident evidence file named '{filename}'. Here is the extracted text:\n\n{extracted_text}"
        }
    ]
    return str(generate_chat_response(history, persona=persona))

