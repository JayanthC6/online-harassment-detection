import re
import json
import datetime

def parse_whatsapp_txt(file_path):
    messages = []
    # Matches both [12/31/22, 10:45:12 AM] and 12/31/22, 10:45 - 
    # Group 1: timestamp, Group 2: sender, Group 3: message
    pattern = re.compile(r'^\[?(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{1,4}[, ]+\d{1,2}:\d{2}(?::\d{2})?(?:[ \u202f]*[aApP][mM])?)\]?[ \-]*([^:]+):\s+(.*)$')
    
    # Detects lines that start with a timestamp but have no colon, which are system messages
    sys_pattern = re.compile(r'^\[?(\d{1,4}[/\.-]\d{1,2}[/\.-]\d{1,4}[, ]+\d{1,2}:\d{2}(?::\d{2})?(?:[ \u202f]*[aApP][mM])?)\]?[ \-]*(.*)$')
    
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
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
                # Check if it's a system message (starts with timestamp but no colon for sender)
                sys_match = sys_pattern.match(line)
                if sys_match:
                    # It's a system message, ignore it
                    continue
                else:
                    # It's a multi-line continuation
                    if messages:
                        messages[-1]["text"] += "\n" + line
                        
    if not messages:
        raise ValueError("This doesn't look like a WhatsApp export.")
        
    return messages

def parse_instagram_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        raise ValueError("This doesn't look like a valid JSON file.")
        
    messages = []
    # Instagram "Download Your Information" format usually has a "messages" array
    raw_messages = data.get("messages", []) if isinstance(data, dict) else []
    if not raw_messages and isinstance(data, list):
        raw_messages = data
        
    if not isinstance(raw_messages, list) or not raw_messages:
        raise ValueError("This doesn't look like an Instagram export.")
        
    for msg in raw_messages:
        content = msg.get("content", "")
        # Apply Meta Latin-1 encoding fix safely
        try:
            content = content.encode('latin1').decode('utf8')
        except Exception:
            pass # Fail safe to original string
            
        sender = msg.get("sender_name", "Unknown")
        try:
            sender = sender.encode('latin1').decode('utf8')
        except Exception:
            pass
            
        # Convert timestamp
        timestamp_ms = msg.get("timestamp_ms")
        timestamp = str(timestamp_ms) if timestamp_ms else ""
        if timestamp_ms:
            try:
                timestamp = datetime.datetime.fromtimestamp(timestamp_ms / 1000.0).isoformat()
            except Exception:
                pass
            
        if content:
            messages.append({
                "sender": sender,
                "text": content,
                "timestamp": timestamp
            })
            
    if not messages:
        raise ValueError("This doesn't look like an Instagram export.")
        
    # Sort messages chronologically as Instagram JSON is sometimes reverse chronological
    messages.sort(key=lambda x: x.get("timestamp", ""))
    return messages
