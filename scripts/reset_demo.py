"""
ShieldAI Demo Database Reset Script

Safely backs up the current persistent database, wipes the database,
recreates fresh tables, and populates the canonical demo dataset.

Usage:
    python scripts/reset_demo.py
"""

import os
import sys
import shutil
from datetime import datetime

# Ensure project root and backend are on PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from core.database import db_instance, Base, ReportModel
from scripts.seed_demo_data import seed


def reset_demo_database():
    db_file = os.path.join(BACKEND_DIR, "data", "shieldai.db")
    print("=" * 75)
    print(">>> [SHIELDAI] DEMO DATABASE RESET & HYGIENE UTILITY")
    print("=" * 75)

    # 1. Backup existing database if it exists
    if os.path.exists(db_file):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(BACKEND_DIR, "data", f"shieldai_backup_{timestamp}.db")
        shutil.copy2(db_file, backup_file)
        print(f"[+] Backup created successfully at:\n    {backup_file}")
    else:
        print("[*] No existing shieldai.db found to backup. Creating fresh instance.")

    # 2. Close active sessions and drop/recreate all tables cleanly
    engine = db_instance._engine
    db_instance._session_factory.remove()
    print("[*] Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("[*] Creating clean database schema...")
    Base.metadata.create_all(bind=engine)

    # 3. Seed demo data
    print("[*] Loading canonical demo dataset...")
    seed(force=True)

    # 4. Verify canonical categories and stats summation
    stats = db_instance.get_stats()
    breakdown = stats.get("category_breakdown", {})
    total = stats.get("total_reports", 0)
    high = stats.get("high_risk", 0)
    med = stats.get("medium_risk", 0)
    safe = stats.get("safe_messages", 0)
    unsupp = stats.get("unsupported", 0)
    tier_sum = high + med + safe + unsupp

    print("\n" + "=" * 75)
    print(">>> DEMO DATABASE VERIFICATION")
    print("=" * 75)
    print(f"Total Incidents:     {total}")
    print(f"High Risk:          {high}")
    print(f"Medium Risk:        {med}")
    print(f"Safe / Low:         {safe}")
    print(f"Unsupported:        {unsupp}")
    print(f"Sum of Tiers:       {tier_sum} ({'MATCHES TOTAL' if tier_sum == total else 'MISMATCH'})")
    print(f"\nCanonical Category Breakdown:")
    for cat, count in sorted(breakdown.items()):
        print(f"  * {cat:20s}: {count} reports")

    # Check for case duplicates
    lower_keys = [k.lower() for k in breakdown.keys()]
    has_duplicates = len(lower_keys) != len(set(lower_keys))
    print(f"\nCase Duplicate Check: {'PASSED (No duplicates)' if not has_duplicates else 'FAILED (Case duplicates found)'}")
    print("=" * 75)
    print("[SUCCESS] Demo database successfully reset and verified.")


if __name__ == "__main__":
    reset_demo_database()

