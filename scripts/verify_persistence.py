"""
Test script verifying that data persists across process restarts in SQLite.
"""
import sys
import os

# Ensure backend directory is in PYTHONPATH
sys.path.insert(0, os.path.abspath("backend"))

from core.database import Database
import db

def step1_write():
    print("=== Step 1: Writing test data to SQLite ===")
    d = Database()
    
    # 1. Log report
    rep_id = d.log_message({
        "id": "persist-test-rep-001",
        "content": "This is a persistent threat test message",
        "actor_id": "persist_actor_99",
        "category": "threat",
        "risk_score": 85.5,
        "severity_tier": "High",
        "label": "harassing",
        "source": "platform"
    })
    print(f"Logged report: {rep_id}")
    
    # 2. Add complaint
    cid = d.add_complaint({
        "id": "persist-test-comp-001",
        "user_id": "victim_user_42",
        "text": "Harasser sent threatening SMS",
        "category": "Harassment",
        "severity_tier": "High"
    })
    print(f"Added complaint: {cid}")
    
    # 3. Save offender profile
    d.save_profile({
        "actor_id": "persist_actor_99",
        "first_seen": "2026-11-01T10:00:00Z",
        "last_seen": "2026-11-02T12:00:00Z",
        "total_reports": 5,
        "harmful_messages": 5,
        "highest_risk": 92.0,
        "behavior_score": 88.0,
        "behavior_level": "Severe",
        "status": "active"
    })
    print("Saved offender profile: persist_actor_99")
    print("Step 1 complete.\n")

def step2_verify():
    print("=== Step 2: Simulating server restart and verifying persistence ===")
    # Create brand new Database connection in fresh state
    d = Database()
    
    # Check report
    rep = d.get_incident("persist-test-rep-001")
    assert rep is not None, "Report was NOT found after restart!"
    assert rep["actor_id"] == "persist_actor_99", f"Unexpected actor_id: {rep.get('actor_id')}"
    print(f"[PASS] Report persisted: {rep['id']} | {rep['text_preview']} | Risk: {rep['risk_score']}")
    
    # Check complaint
    comps = d.get_complaints()
    matching_comp = next((c for c in comps if c["id"] == "persist-test-comp-001"), None)
    assert matching_comp is not None, "Complaint was NOT found after restart!"
    print(f"[PASS] Complaint persisted: {matching_comp['id']} | {matching_comp['text']} | Category: {matching_comp['category']}")
    
    # Check offender profile
    prof = d.get_profile("persist_actor_99")
    assert prof is not None, "Offender profile was NOT found after restart!"
    assert prof["highest_risk"] == 92.0, f"Unexpected highest_risk: {prof.get('highest_risk')}"
    assert prof["behavior_level"] == "Severe", f"Unexpected behavior_level: {prof.get('behavior_level')}"
    print(f"[PASS] Offender persisted: {prof['actor_id']} | Risk: {prof['highest_risk']} | Level: {prof['behavior_level']}")
    
    print("\nALL PERSISTENCE CHECKS PASSED: Reports, complaints, and offenders survive restart!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        step2_verify()
    else:
        step1_write()

