import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from services.parsers import parse_whatsapp_txt, parse_instagram_json
from services.guidance_service import GuidanceService

def test_whatsapp_parser():
    print("Testing WhatsApp Parser...")
    content = """12/31/22, 10:45 - Messages to this chat and calls are now secured with end-to-end encryption.
12/31/22, 10:46 - John Doe: Hey!
12/31/22, 10:47 - Jane Smith: Hello John.
This is a second line of the message.
And a third line.
12/31/22, 10:48 - John Doe: Wow, multi-line works?
"""
    tmp_path = "tmp_wa_test.txt"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    messages = parse_whatsapp_txt(tmp_path)
    os.remove(tmp_path)
    
    assert len(messages) == 3, f"Expected 3 messages, got {len(messages)}"
    assert messages[1]["sender"] == "Jane Smith"
    assert "second line" in messages[1]["text"] and "third line" in messages[1]["text"], "Multi-line failed"
    assert messages[2]["sender"] == "John Doe"
    print("WhatsApp Parser tests passed.")

def test_malformed_whatsapp():
    print("Testing Malformed WhatsApp Parser...")
    content = "This is just random text with no format."
    tmp_path = "tmp_malformed_wa.txt"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    try:
        parse_whatsapp_txt(tmp_path)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert str(e) == "This doesn't look like a WhatsApp export."
    os.remove(tmp_path)
    print("Malformed WhatsApp test passed.")

def test_instagram_parser():
    print("Testing Instagram Parser...")
    
    # Simulate a corrupted UTF-8 string that Meta outputs as latin1
    # For example, 😂 is \xf0\x9f\x98\x82 in utf8. If decoded as latin1, it looks like ð
    corrupted_emoji = "Hello \xf0\x9f\x98\x82"
    
    data = {
        "messages": [
            {
                "sender_name": "InstaUser",
                "timestamp_ms": 1672502400000,
                "content": corrupted_emoji
            }
        ]
    }
    
    tmp_path = "tmp_ig_test.json"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
        
    messages = parse_instagram_json(tmp_path)
    os.remove(tmp_path)
    
    assert len(messages) == 1
    # Expect it to decode back to utf-8 emoji
    assert "😂" in messages[0]["text"], f"Encoding fix failed, got: {messages[0]['text'].encode('utf-8')}"
    print("Instagram Parser tests passed.")

def test_malformed_instagram():
    print("Testing Malformed Instagram Parser...")
    # Test invalid JSON
    tmp_path = "tmp_malformed_ig.json"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write("Not a json file")
        
    try:
        parse_instagram_json(tmp_path)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "valid JSON file" in str(e)
        
    # Test valid JSON but no messages
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump({"random": "data"}, f)
        
    try:
        parse_instagram_json(tmp_path)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "look like an Instagram export" in str(e)
        
    os.remove(tmp_path)
    print("Malformed Instagram test passed.")

def test_guidance_logic():
    print("Testing Guidance Logic...")
    # Plain text regression check (default generic)
    guidance1 = GuidanceService.get_guidance("Offensive Language", 0.9, {}, 50)
    assert guidance1["platform_name"] == "General"
    assert guidance1["show_critical_resources"] == False, "Offensive Language at 50 risk should not show critical resources"

    # Threat (Always Critical)
    guidance2 = GuidanceService.get_guidance("Threat", 0.4, {}, 90, "whatsapp")
    assert guidance2["platform_name"] == "WhatsApp"
    assert guidance2["show_critical_resources"] == True, "Threat should trigger critical even at low conf/high risk"

    # Secondary Critical label
    guidance3 = GuidanceService.get_guidance("Offensive Language", 0.9, {"Extortion": 0.3}, 60)
    assert guidance3["show_critical_resources"] == True, "Secondary Extortion should trigger critical resources"

    # Confidence Gated (Cyberbullying)
    guidance4 = GuidanceService.get_guidance("Cyberbullying", 0.6, {}, 70)
    assert guidance4["show_critical_resources"] == False, "Cyberbullying < 0.7 and risk < 80 should not trigger"
    
    guidance5 = GuidanceService.get_guidance("Cyberbullying", 0.75, {}, 75)
    assert guidance5["show_critical_resources"] == True, "Cyberbullying >= 0.7 should trigger"

    print("Guidance Logic tests passed.")

if __name__ == "__main__":
    test_whatsapp_parser()
    test_malformed_whatsapp()
    test_instagram_parser()
    test_malformed_instagram()
    test_guidance_logic()
    print("ALL TESTS PASSED.")
