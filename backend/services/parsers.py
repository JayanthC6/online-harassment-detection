import re
import json
import datetime
import csv
import os

def parse_whatsapp_txt(file_path):
    messages = []
    # Matches:
    # 1. [12/31/22, 10:45:12 AM] Sender: Message
    # 2. 12/31/22, 10:45 - Sender: Message
    # 3. 31/12/2022, 22:45 - Sender: Message
    # 4. [2022-12-31 10:45:12] Sender: Message
    pattern = re.compile(
        r'^\[?(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{1,4}[, ]+\d{1,2}:\d{2}(?::\d{2})?(?:[ \u202f]*[aApP][mM])?)\]?[ \-]*([^:]+?):\s+(.*)$'
    )
    sys_pattern = re.compile(
        r'^\[?(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{1,4}[, ]+\d{1,2}:\d{2}(?::\d{2})?(?:[ \u202f]*[aApP][mM])?)\]?[ \-]*(.*)$'
    )
    
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
                
            match = pattern.match(line)
            if match:
                timestamp = match.group(1).strip()
                sender = match.group(2).strip()
                text = match.group(3).strip()
                messages.append({
                    "timestamp": timestamp,
                    "sender": sender,
                    "text": text
                })
            else:
                sys_match = sys_pattern.match(line)
                if sys_match:
                    continue  # system announcement
                elif messages:
                    # Multi-line message continuation
                    messages[-1]["text"] += "\n" + line
                        
    if not messages:
        # Fallback for plain lines
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = [l.strip() for l in f if l.strip()]
            if lines:
                for idx, l in enumerate(lines):
                    messages.append({
                        "sender": f"User_{idx % 2 + 1}",
                        "text": l,
                        "timestamp": ""
                    })
    if not messages:
        raise ValueError("Could not parse WhatsApp export or empty text file.")
        
    return messages


def parse_instagram_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f"Invalid JSON file: {e}")
        
    messages = []
    raw_messages = data.get("messages", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    
    if not isinstance(raw_messages, list) or not raw_messages:
        raise ValueError("This doesn't look like an Instagram export (missing 'messages' array).")
        
    for msg in raw_messages:
        content = msg.get("content", "")
        try:
            content = content.encode('latin1').decode('utf8')
        except Exception:
            pass
            
        sender = msg.get("sender_name", "Unknown")
        try:
            sender = sender.encode('latin1').decode('utf8')
        except Exception:
            pass
            
        timestamp_ms = msg.get("timestamp_ms")
        timestamp = ""
        if timestamp_ms:
            try:
                timestamp = datetime.datetime.fromtimestamp(timestamp_ms / 1000.0, tz=datetime.timezone.utc).isoformat()
            except Exception:
                timestamp = str(timestamp_ms)
            
        if content:
            messages.append({
                "sender": sender,
                "text": content,
                "timestamp": timestamp
            })
            
    if not messages:
        raise ValueError("No valid message texts found in Instagram export.")
        
    messages.sort(key=lambda x: x.get("timestamp", ""))
    return messages


def parse_telegram_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f"Invalid Telegram JSON: {e}")
        
    messages = []
    raw_messages = data.get("messages", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    
    for msg in raw_messages:
        if not isinstance(msg, dict):
            continue
        # Extract sender
        sender = msg.get("from") or msg.get("actor") or "Unknown"
        # Extract text (can be string or mixed formatting list)
        text_val = msg.get("text", "")
        if isinstance(text_val, list):
            parts = []
            for item in text_val:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
            text_str = "".join(parts).strip()
        else:
            text_str = str(text_val).strip()
            
        date_str = msg.get("date", "")
        if text_str:
            messages.append({
                "sender": sender,
                "text": text_str,
                "timestamp": date_str
            })
            
    if not messages:
        raise ValueError("No valid messages found in Telegram export.")
        
    return messages


def parse_csv_messages(file_path):
    messages = []
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV is empty or missing headers.")
        
        # Determine sender and text column names
        cols = {c.lower(): c for c in reader.fieldnames}
        text_col = cols.get("text") or cols.get("message") or cols.get("content") or cols.get("comment_text")
        sender_col = cols.get("sender") or cols.get("author") or cols.get("user") or cols.get("actor_id")
        time_col = cols.get("timestamp") or cols.get("date") or cols.get("time")
        
        if not text_col:
            # Fall back to the longest column or second column
            text_col = reader.fieldnames[-1]
            
        for row in reader:
            txt = row.get(text_col, "").strip()
            sndr = row.get(sender_col, "Sender").strip() if sender_col else "User"
            tme = row.get(time_col, "").strip() if time_col else ""
            if txt:
                messages.append({
                    "sender": sndr or "User",
                    "text": txt,
                    "timestamp": tme
                })
                
    if not messages:
        raise ValueError("No message rows found in CSV.")
    return messages


def parse_chat_export(file_path, filename=""):
    """Auto-detect and parse WhatsApp, Instagram, Telegram, CSV, JSON, or TXT."""
    ext = (filename.rsplit(".", 1)[-1].lower() if "." in filename else "").strip()
    if not ext:
        ext = (file_path.rsplit(".", 1)[-1].lower() if "." in file_path else "").strip()

    if ext == "json":
        # Check if Telegram or Instagram
        try:
            return parse_telegram_json(file_path)
        except Exception:
            try:
                return parse_instagram_json(file_path)
            except Exception as e:
                # Try generic messages list
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    data = json.load(f)
                if isinstance(data, list):
                    res = []
                    for item in data:
                        if isinstance(item, dict) and ("text" in item or "content" in item):
                            res.append({
                                "sender": item.get("sender") or item.get("author") or "User",
                                "text": item.get("text") or item.get("content"),
                                "timestamp": item.get("timestamp", "")
                            })
                    if res:
                        return res
                raise ValueError(f"Could not parse JSON chat export: {e}")

    elif ext == "csv":
        return parse_csv_messages(file_path)
        
    elif ext in ("txt", "log", ""):
        return parse_whatsapp_txt(file_path)
        
    else:
        raise ValueError(f"Unsupported chat export format: .{ext}")


def analyze_chat_messages(messages: list, platform: str = "generic") -> dict:
    """
    Takes parsed chat messages, runs detection engine on each message,
    attributes scores to senders, identifies top offender, and computes overall risk.
    """
    if not messages:
        raise ValueError("No messages to analyze.")

    from services.model_service import ModelService
    svc = ModelService.get_instance()

    scored_messages = []
    sender_stats = {}

    for msg in messages:
        sender = msg.get("sender") or "Unknown"
        text = msg.get("text") or ""
        timestamp = msg.get("timestamp") or ""

        if not text.strip():
            continue

        res = svc.analyze(text)
        score = float(res.get("score", 0.0))
        level = res.get("level", "low")
        cat_scores = res.get("category_scores", {})
        signals = res.get("signals", [])
        explanation = res.get("explanation", "")

        scored_item = {
            "sender": sender,
            "text": text,
            "timestamp": timestamp,
            "risk_score": score,
            "level": level,
            "category_scores": cat_scores,
            "signals": signals,
            "explanation": explanation
        }
        scored_messages.append(scored_item)

        # Attribute to sender
        if sender not in sender_stats:
            sender_stats[sender] = {
                "sender": sender,
                "total_messages": 0,
                "flagged_messages": 0,
                "peak_risk": 0.0,
                "total_risk": 0.0,
                "avg_risk": 0.0,
                "categories": set(),
                "primary_violations": []
            }

        st = sender_stats[sender]
        st["total_messages"] += 1
        st["total_risk"] += score
        if score >= 35.0:
            st["flagged_messages"] += 1
        if score > st["peak_risk"]:
            st["peak_risk"] = score

        for cat, cscore in cat_scores.items():
            if cscore >= 40.0:
                st["categories"].add(cat)

    # Finalize sender stats
    for sender, st in sender_stats.items():
        if st["total_messages"] > 0:
            st["avg_risk"] = round(st["total_risk"] / st["total_messages"], 1)
        st["peak_risk"] = round(st["peak_risk"], 1)
        st["categories"] = sorted(list(st["categories"]))
        st["primary_violations"] = st["categories"]
        st.pop("total_risk", None)

    # Top offender is sender with highest peak_risk and most flagged messages
    top_offender = None
    if sender_stats:
        top_offender = max(
            sender_stats.values(),
            key=lambda x: (x["peak_risk"], x["flagged_messages"])
        )

    # Conversation level risk
    all_scores = [m["risk_score"] for m in scored_messages]
    conversation_risk = max(all_scores) if all_scores else 0.0

    if conversation_risk >= 85.0:
        overall_level = "critical"
    elif conversation_risk >= 70.0:
        overall_level = "high"
    elif conversation_risk >= 35.0:
        overall_level = "medium"
    else:
        overall_level = "low"

    advice = [
        "Preserve this unedited chat export file as evidence (keep original timestamps and sender IDs).",
        "Block the harassing sender on the platform to prevent further communication.",
        "Document incidents with screenshots showing user handles, phone numbers, and profile links.",
        "For urgent threats or blackmail, contact emergency services: Dial 112 (National Emergency) or 1930 (Cyber Financial Fraud / Cybercrime Helpline in India).",
        "File an official complaint online at https://cybercrime.gov.in."
    ]

    return {
        "file_type": "chat_export",
        "platform": platform,
        "total_messages": len(scored_messages),
        "risk_score": round(conversation_risk, 1),
        "level": overall_level,
        "top_offender": (top_offender["sender"] if top_offender else "None"),
        "top_offender_detail": top_offender,
        "sender_attribution": sender_stats,
        "messages": scored_messages,
        "advice": advice
    }
