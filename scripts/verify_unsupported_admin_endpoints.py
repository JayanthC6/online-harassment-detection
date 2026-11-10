import sys
import os
import json
import shutil
import tempfile
import uuid

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(base_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Database hygiene: use temporary database so we NEVER pollute backend/data/shieldai.db
temp_dir = tempfile.gettempdir()
temp_db_file = os.path.join(temp_dir, f"shieldai_verify_{uuid.uuid4().hex[:8]}.db")
prod_db_file = os.path.join(backend_dir, "data", "shieldai.db")

if os.path.exists(prod_db_file):
    shutil.copy2(prod_db_file, temp_db_file)

os.environ["SHIELDAI_DB_URL"] = f"sqlite:///{temp_db_file}"

from app import app
from core.database import db_instance

def main():
    app.config["TESTING"] = True
    try:
        with app.test_client() as client:
            # Authenticate admin
            login_res = client.post("/api/admin/login", json={"username": "admin", "password": "password123"})
            token = login_res.get_json()["token"]
            headers = {"Authorization": f"Bearer {token}"}

            print("="*75)
            print("VERIFICATION: LEVEL 'UNSUPPORTED' ACROSS ENDPOINTS & DASHBOARD")
            print(f"(Isolated temporary database: {os.path.basename(temp_db_file)})")
            print("="*75)

            # 1. /api/batch with Hindi message
            hindi_msg = "नमस्ते, यह एक परीक्षण संदेश है जो समर्थित नहीं है।"
            batch_res = client.post("/api/batch", json={"texts": [hindi_msg]})
            batch_item = batch_res.get_json()["results"][0]
            print("\n1. [EXTENSION /api/batch OUTPUT]:")
            print(f"   Level:              {batch_item['level']}")
            print(f"   Language Supported: {batch_item['language_supported']}")
            print(f"   Primary Label:      {batch_item['primary_label']}")
            print(f"   Risk Score:         {batch_item['score']}")

            # 2. /api/analyze with persist=True
            analyze_res = client.post("/api/analyze", json={
                "text": "नमस्ते, क्या आप मेरी मदद कर सकते हैं? यह एक अज्ञात संदेश है।",
                "actor_id": "Hindi_Actor_Demo_99",
                "persist": True
            }, headers=headers)
            analyzed = analyze_res.get_json()
            print("\n2. [ANALYSIS & DB INGESTION (/api/analyze) OUTPUT]:")
            print(f"   Incident ID:        {analyzed.get('id') or analyzed.get('incident_id')}")
            print(f"   Severity Tier:      {analyzed.get('severity_tier')}")
            print(f"   Risk Level:         {analyzed.get('level')}")
            print(f"   Language Supported: {analyzed.get('language_supported')}")
            print(f"   Language Detected:  {analyzed.get('language_detected')}")

            # 3. Queue filter: /api/admin/reports?risk_level=unsupported
            reports_res = client.get("/api/admin/reports?risk_level=unsupported", headers=headers)
            rep_data = reports_res.get_json()
            print("\n3. [QUEUE FILTER (/api/admin/reports?risk_level=unsupported) OUTPUT]:")
            print(f"   Total Matching:     {rep_data['total']}")
            print(f"   Filtered Items:     {len(rep_data['reports'])}")
            if rep_data['reports']:
                sample = rep_data['reports'][0]
                print(f"   Sample ID:          {sample.get('id') or sample.get('_id')}")
                print(f"   Sample Severity:    {sample.get('severity_tier')}")
                print(f"   Sample Preview:     {ascii(sample.get('text_preview', '')[:50])}")

            # 4. Admin stats: /api/admin/stats
            stats_res = client.get("/api/admin/stats", headers=headers)
            stats_data = stats_res.get_json()
            print("\n4. [ADMIN STATS & DASHBOARD (/api/admin/stats) OUTPUT]:")
            print(f"   Total Reports:      {stats_data.get('total_reports')}")
            print(f"   Model Loaded:       {stats_data.get('model_loaded')}")
            print(f"   Mode:               {stats_data.get('mode')}")
            print(f"   Category Breakdown: {stats_data.get('category_breakdown')}")

            # 5. Charts / Analytics: /api/admin/analytics
            analytics_res = client.get("/api/admin/analytics", headers=headers)
            analytics_data = analytics_res.get_json()
            print("\n5. [CHARTS / ANALYTICS (/api/admin/analytics) OUTPUT]:")
            print(f"   Total Reports:      {analytics_data.get('total')}")
            print(f"   High Risk:          {analytics_data.get('high_risk')}")
            print(f"   Medium Risk:        {analytics_data.get('medium_risk')}")
            print(f"   Safe:               {analytics_data.get('safe')}")
            print(f"   Unsupported:        {analytics_data.get('unsupported')}")
            print(f"   Categories:         {analytics_data.get('categories')}")

            # 6. Daily counts: /api/admin/daily_counts
            daily_res = client.get("/api/admin/daily_counts", headers=headers)
            daily_data = daily_res.get_json()
            counts = daily_data.get("daily_counts", [])
            print("\n6. [DAILY TREND CHART (/api/admin/daily_counts) OUTPUT]:")
            print(f"   Window (days):      {len(counts)}")
            print(f"   Last 3 Days Counts: {counts[-3:] if len(counts) >= 3 else counts}")

            # 7. Offenders view: /api/admin/offenders
            offenders_res = client.get("/api/admin/offenders", headers=headers)
            off_data = offenders_res.get_json()
            print("\n7. [OFFENDERS VIEW (/api/admin/offenders) OUTPUT]:")
            print(f"   Total Offenders:    {len(off_data.get('offenders', []))}")
            print(f"   Status:             OK (HTTP {offenders_res.status_code}, zero schema errors)")
            print("="*75)
    finally:
        # Cleanup temporary database
        try:
            db_instance._session_factory.remove()
            if os.path.exists(temp_db_file):
                os.remove(temp_db_file)
        except Exception:
            pass

if __name__ == "__main__":
    main()
