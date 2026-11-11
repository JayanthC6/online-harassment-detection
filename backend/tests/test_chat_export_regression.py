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


def test_chat_export_offender_tracking_upload_twice(client):
    """
    Item 1: Verify chat export tracking:
    - Non-private upload records flagged senders (Sam) as offender entities (+1 hit per flagged message).
    - Unflagged senders (Raj, Priya) must NOT be recorded.
    - Uploading the exact same chat twice must increase Sam's hit count (+4 -> 8).
    - Conversation record must be visible in get_conversations and get_stats.
    """
    from core.database import db_instance, OffenderModel, ConversationModel
    session = db_instance.get_session()
    try:
        # Clean any prior records for Sam, Raj, Priya
        session.query(OffenderModel).filter(OffenderModel.entity_value.in_(["Sam", "Raj", "Priya"])).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()

    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".txt", encoding="utf-8") as f:
        f.write(CHAT_CONTENT)
        f_path = f.name

    try:
        # Initial stats
        stats_before = db_instance.get_stats()
        conv_count_before = stats_before["conversation_stats"]["total"]

        # --- FIRST UPLOAD ---
        with open(f_path, "rb") as upload_file:
            res1 = client.post(
                "/api/predict/conversation/import",
                data={"file": (upload_file, "raj_sam_priya_chat.txt"), "persist": "true"},
                content_type="multipart/form-data"
            )
        assert res1.status_code == 200, f"Upload 1 failed: {res1.data}"
        
        # Check Sam after 1st upload
        sam1 = db_instance.get_offender_by_value("Sam")
        assert sam1 is not None, "Sam should be recorded as an offender entity"
        assert sam1["entity_type"] == "sender"
        assert sam1["hit_count"] == 4, f"Sam should have 4 hits after first upload, got {sam1['hit_count']}"
        assert len(sam1["related_reports"]) == 1
        assert len(sam1["timeline"]) == 4

        # Raj and Priya must NOT be recorded
        assert db_instance.get_offender_by_value("Raj") is None, "Raj (unflagged) must not be recorded"
        assert db_instance.get_offender_by_value("Priya") is None, "Priya (unflagged) must not be recorded"

        # Conversation is in get_conversations and counted in stats
        convs1 = db_instance.get_conversations()
        assert any(c["id"] == sam1["related_reports"][0] for c in convs1["conversations"]), "Conversation must be visible in queue"
        stats1 = db_instance.get_stats()
        assert stats1["conversation_stats"]["total"] == conv_count_before + 1

        # --- SECOND UPLOAD OF SAME CHAT ---
        with open(f_path, "rb") as upload_file:
            res2 = client.post(
                "/api/predict/conversation/import",
                data={"file": (upload_file, "raj_sam_priya_chat.txt"), "persist": "true"},
                content_type="multipart/form-data"
            )
        assert res2.status_code == 200, f"Upload 2 failed: {res2.data}"

        # Check Sam after 2nd upload: hit count must double (+4 -> 8)
        sam2 = db_instance.get_offender_by_value("Sam")
        assert sam2 is not None
        assert sam2["hit_count"] == 8, f"Sam should have 8 hits after second upload, got {sam2['hit_count']}"
        assert len(sam2["related_reports"]) == 2, f"Expected 2 linked reports, got {len(sam2['related_reports'])}"
        assert len(sam2["timeline"]) == 8, f"Expected 8 timeline entries, got {len(sam2['timeline'])}"

        # Raj and Priya must STILL not be recorded
        assert db_instance.get_offender_by_value("Raj") is None, "Raj must still not be recorded"
        assert db_instance.get_offender_by_value("Priya") is None, "Priya must still not be recorded"

        # Stats increased by 2
        stats2 = db_instance.get_stats()
        assert stats2["conversation_stats"]["total"] == conv_count_before + 2
    finally:
        if os.path.exists(f_path):
            os.remove(f_path)


