import os
import tempfile
import pytest
from services.parsers import parse_whatsapp_txt
from services.prediction_service import PredictionService

CHAT_CONTENT = """12/03/2024, 10:01 - Raj: hey are you coming tomorrow?
12/03/2024, 10:02 - Sam: you're so ugly and stupid
12/03/2024, 10:03 - Sam: nobody wants you here, loser
12/03/2024, 10:04 - Raj: please stop messaging me
12/03/2024, 10:05 - Sam: I know where you live
12/03/2024, 10:06 - Sam: send me 5000 or I leak your photos
12/03/2024, 10:07 - Priya: Raj, ignore him, I'll help you report this"""

def test_chat_export_flagged_actors_regression():
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".txt", encoding="utf-8") as f:
        f.write(CHAT_CONTENT)
        f_path = f.name

    try:
        messages = parse_whatsapp_txt(f_path)
        assert len(messages) == 7

        result = PredictionService.analyze_conversation(messages)
        actor_intel = result.get("actor_intelligence", {})

        # 1. Raj and Priya must have 0 flagged messages
        assert actor_intel["Raj"]["flagged_messages"] == 0, f"Raj should have 0 flagged, got {actor_intel['Raj']['flagged_messages']}"
        assert actor_intel["Priya"]["flagged_messages"] == 0, f"Priya should have 0 flagged, got {actor_intel['Priya']['flagged_messages']}"

        # 2. Sam must have all 4 messages flagged
        assert actor_intel["Sam"]["flagged_messages"] == 4, f"Sam should have 4 flagged, got {actor_intel['Sam']['flagged_messages']}"
        assert actor_intel["Sam"]["risk_concentration_percentage"] == 100.0

        # 3. Top category must be Threat or Blackmail/Sextortion (never Hate Speech)
        primary = result.get("primary_label", "").lower()
        assert any(t in primary for t in ["threat", "blackmail", "sextortion"]), f"Primary label expected Threat or Blackmail/Sextortion, got: {result.get('primary_label')}"
        assert "hate speech" not in primary

        # 4. Escalation level must be consistent and explain risk jump
        assert result.get("escalation_level") in ["High", "Medium"]
        for reason in result.get("escalation_reason", []):
            assert "Severe" not in reason

        # 5. Top evidence must replace generic 'Flagged by automated safety checks'
        reasons = result.get("flagging_reasons", [])
        assert "Flagged by automated safety checks." not in reasons
        assert any("[Sam]" in r for r in reasons)
    finally:
        if os.path.exists(f_path):
            os.remove(f_path)

