"""
Comprehensive Phase 3 validation script for ShieldAI.
Tests all Phase 3 requirements end-to-end:
1. Text analysis: POST /api/analyze
2. Batch processing: POST /api/batch (verifies stores nothing)
3. Chatbot: POST /api/chat
4. Chat export parsing & sender attribution: WhatsApp, Telegram, CSV exports
5. Document & media analysis: PDF, missing tool detection (Tesseract OCR message)
6. Repeat offender tracking: senders, URLs, phone numbers, emails across reports
7. Admin endpoints: /api/admin/reports, /api/admin/stats, /api/admin/offenders, /api/admin/status
"""
import sys
import os
import io
import json
import tempfile

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(base_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import app
from core.database import db_instance
from services.auth_service import AuthService
from services.offender_service import OffenderService

def run_tests():
    client = app.test_client()
    passed = 0
    total = 0

    def check(name, condition, extra=""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name} {extra}")
        else:
            print(f"  [FAIL] {name} {extra}")

    print("\n" + "="*80)
    print("PHASE 3 END-TO-END VALIDATION SUITE")
    print("="*80)

    # ── 1. Authentication & Admin JWT ───────────────────────────────────────
    print("\n--- 1. Admin Authentication ---")
    login_res = client.post("/api/admin/login", json={"username": "admin", "password": "password123"})
    check("POST /api/admin/login status=200", login_res.status_code == 200)
    token = login_res.get_json().get("token")
    check("Admin JWT token issued", bool(token and len(token) > 20))
    auth_headers = {"Authorization": f"Bearer {token}"}

    # ── 2. POST /api/analyze (Text) ──────────────────────────────────────────
    print("\n--- 2. POST /api/analyze ---")
    threat_text = "I know where you live and I will murder you tonight. Contact me at phisher@fake-bank.xyz or +919876543210 http://threat-verify.xyz"
    analyze_res = client.post("/api/analyze", json={
        "text": threat_text,
        "persist": True,
        "actor_id": "BadActor_99"
    }, headers=auth_headers)
    check("POST /api/analyze status=200", analyze_res.status_code == 200)
    data = analyze_res.get_json()
    check("Risk score calculated", data.get("risk_score", 0) >= 80)
    check("Threat level critical", data.get("severity_tier") == "Critical")
    check("Category identified", data.get("category") in ["threat", "Threat"])

    # ── 3. POST /api/batch (Extension - stores nothing) ──────────────────────
    print("\n--- 3. POST /api/batch (Stores Nothing) ---")
    count_before = db_instance.get_reports(page_size=1000).get("total", 0)
    batch_res = client.post("/api/batch", json={
        "texts": [
            "Good morning! Have a great day ahead.",
            "You are a stupid idiot and nobody likes you",
            "Urgent: Your SBI account is blocked. Verify at http://scam-sbi.xyz"
        ]
    })
    check("POST /api/batch status=200", batch_res.status_code == 200)
    b_data = batch_res.get_json()
    check("Batch processed 3 items", len(b_data.get("results", [])) == 3)
    count_after = db_instance.get_reports(page_size=1000).get("total", 0)
    check("POST /api/batch stored 0 rows in database", count_before == count_after, f"(before={count_before}, after={count_after})")

    # ── 4. POST /api/chat ────────────────────────────────────────────────────
    print("\n--- 4. POST /api/chat ---")
    chat_res = client.post("/api/chat", json={
        "session_id": "test_session_p3",
        "message": "Someone is sending me blackmail messages threatening to leak photos. What should I do?",
        "persona": "user"
    })
    check("POST /api/chat status=200", chat_res.status_code == 200)
    c_data = chat_res.get_json()
    check("Chatbot returned response", bool(c_data.get("response")))
    check("Session ID preserved", c_data.get("session_id") == "test_session_p3")

    # ── 5. File Support: WhatsApp Chat Export (.txt) ─────────────────────────
    print("\n--- 5. WhatsApp Chat Export Parsing & Sender Attribution ---")
    wa_content = (
        "[12/10/24, 10:15:20] Alice: Hey Bob, are you coming to the group study?\n"
        "[12/10/24, 10:16:01] Bob: Yes, leaving my house in 5 minutes.\n"
        "[12/10/24, 10:17:15] StalkerX: You will regret showing up there. I will find you and break your neck.\n"
        "[12/10/24, 10:18:00] StalkerX: Watch your back loser http://malicious-tracker.xyz\n"
        "[12/10/24, 10:19:10] Alice: Who is this? Stop messaging this group.\n"
    )
    wa_file = (io.BytesIO(wa_content.encode("utf-8")), "whatsapp_export.txt")
    wa_res = client.post("/api/analyze/file", data={"file": wa_file, "persist": "true"}, content_type="multipart/form-data")
    check("POST /api/analyze/file (WhatsApp TXT) status=200", wa_res.status_code == 200)
    wa_data = wa_res.get_json()
    check("Identified as chat export", wa_data.get("file_type") == "chat_export")
    check("Total messages parsed = 5", wa_data.get("total_messages") == 5)
    check("Sender attribution computed", "StalkerX" in wa_data.get("sender_attribution", {}))
    stalker_stats = wa_data.get("sender_attribution", {}).get("StalkerX", {})
    check("Top offender attributed to StalkerX", wa_data.get("top_offender") == "StalkerX")
    check("StalkerX peak risk >= 80", stalker_stats.get("peak_risk", 0) >= 80)
    check("Safety advice with India helplines included", any("1930" in a or "112" in a for a in wa_data.get("advice", [])))

    # ── 6. File Support: Telegram JSON Export ────────────────────────────────
    print("\n--- 6. Telegram JSON Export Parsing ---")
    tg_data_obj = {
        "messages": [
            {"from": "VictimUser", "text": "Can someone help me with the assignment?", "date": "2024-10-12T10:00:00"},
            {"from": "TrollUser", "text": "You are a useless moron and should drop out.", "date": "2024-10-12T10:01:00"},
            {"from": "TrollUser", "text": "Nobody wants you here, disgusting pig.", "date": "2024-10-12T10:02:00"}
        ]
    }
    tg_file = (io.BytesIO(json.dumps(tg_data_obj).encode("utf-8")), "result.json")
    tg_res = client.post("/api/analyze/file", data={"file": tg_file}, content_type="multipart/form-data")
    check("POST /api/analyze/file (Telegram JSON) status=200", tg_res.status_code == 200)
    tg_res_data = tg_res.get_json()
    check("Telegram export parsed 3 messages", tg_res_data.get("total_messages") == 3)
    check("Top offender is TrollUser", tg_res_data.get("top_offender") == "TrollUser")

    # ── 7. File Support: CSV Messages Export ─────────────────────────────────
    print("\n--- 7. CSV Messages Export ---")
    csv_content = (
        "sender,text,timestamp\n"
        "UserA,Hello everyone,2024-10-12 12:00\n"
        "Scammer123,Click here to claim 50000 lottery cash http://fake-lottery.xyz,2024-10-12 12:01\n"
    )
    csv_file = (io.BytesIO(csv_content.encode("utf-8")), "chat.csv")
    csv_res = client.post("/api/analyze/file", data={"file": csv_file}, content_type="multipart/form-data")
    check("POST /api/analyze/file (CSV) status=200", csv_res.status_code == 200)
    csv_res_data = csv_res.get_json()
    check("CSV parsed 2 messages", csv_res_data.get("total_messages") == 2)
    check("Top offender Scammer123 flagged", csv_res_data.get("top_offender") == "Scammer123")

    # ── 8. File Support: PDF Document ────────────────────────────────────────
    print("\n--- 8. PDF Document Extraction (pypdf) ---")
    try:
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        # We test that pypdf creates and reads without error
        pdf_bytes = io.BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)
        pdf_file = (pdf_bytes, "sample.pdf")
        pdf_res = client.post("/api/analyze/file", data={"file": pdf_file}, content_type="multipart/form-data")
        # Empty page returns 400 No text detected in file
        check("PDF reader executed properly", pdf_res.status_code in [200, 400])
    except Exception as e:
        check("PDF execution check", False, str(e))

    # ── 9. Missing Tool Error Handling (Tesseract OCR Binary) ────────────────
    print("\n--- 9. Missing Tool Guidance (Tesseract OCR) ---")
    from PIL import Image
    img = Image.new("RGB", (100, 50), color=(255, 255, 255))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    img_file = (img_bytes, "screenshot.png")
    img_res = client.post("/api/analyze/file", data={"file": img_file}, content_type="multipart/form-data")
    # If tesseract binary is not installed, it should return 422 with clear install message
    img_data = img_res.get_json()
    if img_res.status_code == 422:
        check("Missing OCR binary returns HTTP 422", True)
        check("Clear installation guidance returned in error", "install tesseract" in img_data.get("message", "").lower())
    else:
        # If tesseract binary happened to be present
        check("OCR processed image", img_res.status_code in [200, 400])

    # ── 10. Repeat Offenders Tracking & Admin Endpoints ──────────────────────
    print("\n--- 10. Repeat Offenders & Admin Endpoints ---")
    # Let's seed repeat hits for an offender entity
    OffenderService.track_incident_entities(
        report_id="rep_test_001",
        text="Call our helpline at +919876543210 or visit http://scam-lottery-portal.xyz to collect prize. Email prize@scam-lottery.xyz",
        risk_score=95.0,
        category="scam",
        sender="OffenderAlpha"
    )
    OffenderService.track_incident_entities(
        report_id="rep_test_002",
        text="Final notice: verify KYC at http://scam-lottery-portal.xyz or pay fine via +919876543210",
        risk_score=92.0,
        category="phishing",
        sender="OffenderAlpha"
    )

    # Query GET /api/admin/offenders
    offenders_res = client.get("/api/admin/offenders", headers=auth_headers)
    check("GET /api/admin/offenders status=200", offenders_res.status_code == 200)
    off_data = offenders_res.get_json()
    check("Offenders list returned", isinstance(off_data.get("offenders"), list) and len(off_data["offenders"]) > 0)
    check("Offenders stats returned", "senders" in off_data.get("stats", {}) and "urls" in off_data["stats"])

    # Query single offender detail
    detail_res = client.get("/api/admin/offenders/OffenderAlpha", headers=auth_headers)
    check("GET /api/admin/offenders/<name> status=200", detail_res.status_code == 200)
    detail_data = detail_res.get_json().get("offender", {})
    check("Offender hit count >= 2", detail_data.get("hit_count", 0) >= 2)
    check("Offender peak risk >= 90", detail_data.get("peak_risk", 0) >= 90)
    check("Offender linked reports recorded", len(detail_data.get("related_reports", [])) >= 2)
    check("Offender timeline populated", len(detail_data.get("timeline", [])) >= 2)

    # Check URL offender
    url_res = client.get("/api/admin/offenders/scam-lottery-portal.xyz", headers=auth_headers)
    check("Tracked URL entity across reports", url_res.status_code == 200)

    # Check Phone offender
    phone_res = client.get("/api/admin/offenders/919876543210", headers=auth_headers)
    check("Tracked phone number entity across reports", phone_res.status_code == 200)

    # Update offender status
    up_off_res = client.post("/api/admin/offenders/OffenderAlpha/status", json={"status": "banned", "notes": "Serial extortion offender"}, headers=auth_headers)
    check("POST /api/admin/offenders/<name>/status status=200", up_off_res.status_code == 200)
    check("Offender status updated to banned", up_off_res.get_json().get("new_status") == "banned")

    # ── 11. Admin Reports, Stats, and Status Updates ─────────────────────────
    print("\n--- 11. Admin Reports, Stats, & Status Updates ---")
    reports_res = client.get("/api/admin/reports", headers=auth_headers)
    check("GET /api/admin/reports status=200", reports_res.status_code == 200)
    reports_list = reports_res.get_json().get("reports", [])
    check("Admin reports returned non-empty list", len(reports_list) > 0)

    stats_res = client.get("/api/admin/stats", headers=auth_headers)
    check("GET /api/admin/stats status=200", stats_res.status_code == 200)
    check("Admin stats has total_reports", "total_reports" in stats_res.get_json())

    # Update status of a report
    if reports_list:
        target_rep_id = reports_list[0]["_id"]
        status_res = client.post("/api/admin/status", json={"id": target_rep_id, "status": "resolved"}, headers=auth_headers)
        check("POST /api/admin/status status=200", status_res.status_code == 200)
        check("Report status updated to resolved", status_res.get_json().get("new_status") == "resolved")

    print("\n" + "="*80)
    print(f"PHASE 3 RESULTS: {passed} / {total} tests passed ({passed/total*100:.1f}%)")
    print("="*80)
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

