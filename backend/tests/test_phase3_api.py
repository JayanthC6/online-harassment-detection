import io
import json
import pytest
from app import app
from core.database import db_instance
from services.offender_service import OffenderService

@pytest.fixture(scope="module")
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

@pytest.fixture(scope="module")
def auth_headers(client):
    res = client.post("/api/admin/login", json={"username": "admin", "password": "password123"})
    assert res.status_code == 200
    token = res.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}

def test_admin_auth_and_jwt(client, auth_headers):
    # Valid auth header succeeds
    res = client.get("/api/admin/stats", headers=auth_headers)
    assert res.status_code == 200

    # Missing auth header returns 401
    res_no_auth = client.get("/api/admin/stats")
    assert res_no_auth.status_code == 401

def test_analyze_text_endpoint(client, auth_headers):
    payload = {
        "text": "I know where you live and I will murder you tonight.",
        "actor_id": "BadActor_Threat"
    }
    res = client.post("/api/analyze", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert data["risk_score"] >= 80.0
    assert data["severity_tier"] == "Critical"
    assert data["category"] in ["threat", "Threat"]

def test_batch_extension_stores_nothing(client):
    count_before = db_instance.get_reports(page_size=1000).get("total", 0)
    res = client.post("/api/batch", json={
        "texts": [
            "Good morning!",
            "You are a stupid idiot and nobody likes you",
            "Urgent: your account is suspended http://fake-login.xyz"
        ]
    })
    assert res.status_code == 200
    data = res.get_json()
    assert len(data.get("results", [])) == 3
    count_after = db_instance.get_reports(page_size=1000).get("total", 0)
    assert count_before == count_after, "POST /api/batch must not persist data"

def test_batch_large_payload_60_messages(client):
    texts = [f"Message #{i}: Hello this is test text for 60-message batch verification {i}" for i in range(60)]
    res = client.post("/api/batch", json={"texts": texts})
    assert res.status_code == 200
    data = res.get_json()
    assert len(data.get("results", [])) == 60

def test_whatsapp_chat_export_and_attribution(client):
    wa_content = (
        "[12/10/24, 10:15:20] Alice: Hey Bob, are you coming to the group study?\n"
        "[12/10/24, 10:16:01] Bob: Yes, leaving my house in 5 minutes.\n"
        "[12/10/24, 10:17:15] StalkerX: You will regret showing up there. I will find you and break your neck.\n"
        "[12/10/24, 10:18:00] StalkerX: Watch your back loser http://malicious-tracker.xyz\n"
        "[12/10/24, 10:19:10] Alice: Who is this? Stop messaging this group.\n"
    )
    wa_file = (io.BytesIO(wa_content.encode("utf-8")), "whatsapp_export.txt")
    res = client.post("/api/analyze/file", data={"file": wa_file}, content_type="multipart/form-data")
    assert res.status_code == 200
    data = res.get_json()
    assert data["file_type"] == "chat_export"
    assert data["total_messages"] == 5
    assert data["top_offender"] == "StalkerX"
    assert "StalkerX" in data["sender_attribution"]
    assert data["sender_attribution"]["StalkerX"]["peak_risk"] >= 80.0
    assert any("1930" in a or "112" in a for a in data.get("advice", []))

def test_telegram_json_export(client):
    tg_data = {
        "messages": [
            {"from": "VictimUser", "text": "Can someone help me with the assignment?", "date": "2024-10-12T10:00:00"},
            {"from": "TrollUser", "text": "You are a useless moron and should drop out.", "date": "2024-10-12T10:01:00"},
            {"from": "TrollUser", "text": "Nobody wants you here, disgusting pig.", "date": "2024-10-12T10:02:00"}
        ]
    }
    tg_file = (io.BytesIO(json.dumps(tg_data).encode("utf-8")), "result.json")
    res = client.post("/api/analyze/file", data={"file": tg_file}, content_type="multipart/form-data")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_messages"] == 3
    assert data["top_offender"] == "TrollUser"

def test_missing_ocr_guidance_message(client):
    from PIL import Image
    img = Image.new("RGB", (80, 40), color=(255, 255, 255))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    img_file = (img_bytes, "screenshot.png")
    res = client.post("/api/analyze/file", data={"file": img_file}, content_type="multipart/form-data")
    # If tesseract binary is missing on system, returns 422 with clear install advice
    if res.status_code == 422:
        data = res.get_json()
        msg = data.get("message", "").lower()
        assert "tesseract" in msg or "rapidocr" in msg
    else:
        assert res.status_code in [200, 400]

def test_repeat_offender_tracking_and_endpoints(client, auth_headers):
    OffenderService.track_incident_entities(
        report_id="rep_test_repeat_01",
        text="Call +919876543210 or visit http://scam-verify-portal.xyz. Contact claim@scam-verify-portal.xyz",
        risk_score=94.0,
        category="scam",
        sender="SerialScammer"
    )
    OffenderService.track_incident_entities(
        report_id="rep_test_repeat_02",
        text="Urgent notice from +919876543210: verify at http://scam-verify-portal.xyz",
        risk_score=91.0,
        category="phishing",
        sender="SerialScammer"
    )

    # List offenders
    res = client.get("/api/admin/offenders", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["offenders"]) > 0

    # Offender detail
    res_det = client.get("/api/admin/offenders/SerialScammer", headers=auth_headers)
    assert res_det.status_code == 200
    offender = res_det.get_json()["offender"]
    assert offender["hit_count"] >= 2
    assert offender["peak_risk"] >= 90.0
    assert len(offender["related_reports"]) >= 2

    # Track URL
    res_url = client.get("/api/admin/offenders/scam-verify-portal.xyz", headers=auth_headers)
    assert res_url.status_code == 200

    # Track Phone
    res_phone = client.get("/api/admin/offenders/919876543210", headers=auth_headers)
    assert res_phone.status_code == 200

    # Update status
    res_up = client.post("/api/admin/offenders/SerialScammer/status", json={"status": "banned", "notes": "Serial threat"}, headers=auth_headers)
    assert res_up.status_code == 200
    assert res_up.get_json()["new_status"] == "banned"

def test_admin_report_status_updates(client, auth_headers):
    # Fetch recent reports
    res = client.get("/api/admin/reports", headers=auth_headers)
    assert res.status_code == 200
    reports = res.get_json().get("reports", [])
    if reports:
        rep_id = reports[0]["_id"]
        res_stat = client.post("/api/admin/status", json={"id": rep_id, "status": "resolved"}, headers=auth_headers)
        assert res_stat.status_code == 200
        assert res_stat.get_json()["new_status"] == "resolved"


def test_unsupported_language_admin_flow(client, auth_headers):
    """
    Verify level 'unsupported' end-to-end:
    - /api/batch returns level 'unsupported' with language_supported=false
    - /api/analyze logs incident with severity_tier 'Unsupported'
    - /api/admin/reports filters by risk_level=unsupported
    - /api/admin/stats, /api/admin/analytics, /api/admin/daily_counts, and /api/admin/offenders
      all execute without error and return expected data.
    """
    # 1. /api/batch with unsupported Hindi message
    hindi_text = "नमस्ते, यह एक परीक्षण संदेश है जो समर्थित नहीं है"
    batch_res = client.post("/api/batch", json={"texts": [hindi_text]})
    assert batch_res.status_code == 200
    batch_data = batch_res.get_json()
    assert batch_data["count"] == 1
    item = batch_data["results"][0]
    assert item["level"] == "unsupported"
    assert item["language_supported"] is False
    assert item["primary_label"] == "Unsupported Language"
    assert item["score"] is None

    # 2. Analyze & persist an unsupported Hindi incident
    analyze_res = client.post("/api/analyze", json={
        "text": "नमस्ते दोस्त, यह केवल एक हिंदी संदेश है।",
        "actor_id": "Hindi_Actor_01",
        "persist": True
    }, headers=auth_headers)
    assert analyze_res.status_code == 200
    analyzed = analyze_res.get_json()
    assert analyzed["level"] == "unsupported"
    assert analyzed["severity_tier"] == "Unsupported"
    assert analyzed["language_supported"] is False

    # 3. Queue filter: query reports by risk_level=unsupported
    rep_res = client.get("/api/admin/reports?risk_level=unsupported", headers=auth_headers)
    assert rep_res.status_code == 200
    reports = rep_res.get_json().get("reports", [])
    assert any(r.get("severity_tier") == "Unsupported" for r in reports)

    # 4. Admin stats & dashboard
    stats_res = client.get("/api/admin/stats", headers=auth_headers)
    assert stats_res.status_code == 200
    stats = stats_res.get_json()
    assert "model_loaded" in stats
    assert stats["total_reports"] >= 1

    # 5. Admin analytics (category and severity charts)
    analytics_res = client.get("/api/admin/analytics", headers=auth_headers)
    assert analytics_res.status_code == 200

    # 6. Daily trend chart
    daily_res = client.get("/api/admin/daily_counts?days=7", headers=auth_headers)
    assert daily_res.status_code == 200
    assert "counts" in daily_res.get_json()

    # 7. Repeat offenders view
    offenders_res = client.get("/api/admin/offenders", headers=auth_headers)
    assert offenders_res.status_code == 200
    assert "offenders" in offenders_res.get_json()


def test_admin_stats_canonical_categories_no_case_duplicates(client, auth_headers):
    """
    Verify:
    1. All category names in /api/admin/stats and /api/admin/analytics belong to the canonical set
    2. No duplicate names differing only by case
    3. The sum invariant holds: high_risk + medium_risk + safe_messages + unsupported == total_reports
    """
    from core.database import CANONICAL_CATEGORIES

    stats_res = client.get("/api/admin/stats", headers=auth_headers)
    assert stats_res.status_code == 200
    stats = stats_res.get_json()

    # Sum invariant check
    assert (
        stats["high_risk"] + stats["medium_risk"] + stats["safe_messages"] + stats["unsupported"]
        == stats["total_reports"]
    ), f"Stats sum invariant violated: {stats}"

    # Category breakdown check
    breakdown = stats.get("category_breakdown", {})
    keys = list(breakdown.keys())
    assert len(keys) == len(set(k.lower() for k in keys)), f"Duplicate categories differing only by case: {keys}"
    for k in keys:
        assert k in CANONICAL_CATEGORIES, f"Non-canonical category found: {k}"

    analytics_res = client.get("/api/admin/analytics", headers=auth_headers)
    assert analytics_res.status_code == 200
    analytics = analytics_res.get_json()
    cats = list(analytics.get("categories", {}).keys())
    assert len(cats) == len(set(c.lower() for c in cats)), f"Duplicate categories in analytics: {cats}"
    for c in cats:
        assert c in CANONICAL_CATEGORIES, f"Non-canonical category in analytics: {c}"



