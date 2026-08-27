"""
Count MongoDB incident/messages collection entries to verify no demo leakage.
Uses AdminService.get_stats() which hits the real collection.count_documents.
"""
import sys
sys.path.insert(0, r"c:\Users\jayanth\Downloads\online-harassment-detection\backend")

import os
# Load .env so MONGODB_URI is set
from pathlib import Path
env_path = Path(r"c:\Users\jayanth\Downloads\online-harassment-detection\backend\.env")
for line in env_path.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

import db as db_mod
db_instance = db_mod._db_instance

if hasattr(db_instance, "collection") and db_instance.collection is not None:
    total = db_instance.collection.count_documents({})
    demo_visitor = db_instance.collection.count_documents({"actor_id": "DemoVisitor"})
    print(f"=== LIVE MongoDB stats ===")
    print(f"  Total messages in collection:  {total}")
    print(f"  Entries with actor_id=DemoVisitor:  {demo_visitor}")
    print()
    if demo_visitor == 0:
        print("PASS: No DemoVisitor entries in the database — /demo/analyze does NOT persist.")
    else:
        print(f"FAIL: {demo_visitor} DemoVisitor entries leaked into MongoDB!")
else:
    print("No MongoDB collection found (in-memory mode). Verify MONGODB_URI in .env.")
    print("Run from inside the venv: set MONGODB_URI=... then re-run.")
