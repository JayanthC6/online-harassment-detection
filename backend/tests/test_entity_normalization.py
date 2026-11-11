"""
Unit and regression tests for Entity Normalisation (Item 2).
Verifies that URLs/domains are normalised (scheme, www, trailing slash stripped, lowercased),
duplicate rows are merged, and full URLs are retained in timeline entries.
"""
import pytest
from services.offender_service import normalize_url_entity, OffenderService
from core.database import db_instance, OffenderModel

def test_normalize_url_entity_logic():
    assert normalize_url_entity("http://sbi-kyc-update.xyz") == "sbi-kyc-update.xyz"
    assert normalize_url_entity("https://www.sbi-kyc-update.xyz/") == "sbi-kyc-update.xyz"
    assert normalize_url_entity("http://WWW.SBI-KYC-UPDATE.XYZ") == "sbi-kyc-update.xyz"
    assert normalize_url_entity("https://paypa1-security.xyz/login/") == "paypa1-security.xyz/login"
    assert normalize_url_entity("sbi-kyc-update.xyz") == "sbi-kyc-update.xyz"

def test_url_entity_recording_combines_hits_and_preserves_example():
    session = db_instance.get_session()
    try:
        session.query(OffenderModel).filter(OffenderModel.entity_value.in_(["sbi-kyc-update.xyz", "http://sbi-kyc-update.xyz"])).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()

    # Record hit with http scheme
    off1 = db_instance.record_offender_hit(
        entity_type="url",
        entity_value="http://sbi-kyc-update.xyz",
        risk_score=85.0,
        report_id="rep-1",
        category="phishing",
        snippet="fake banking alert",
        raw_value="http://sbi-kyc-update.xyz/login?user=1"
    )
    assert off1["entity_value"] == "sbi-kyc-update.xyz"
    assert off1["hit_count"] == 1
    assert off1["timeline"][0]["example_url"] == "http://sbi-kyc-update.xyz/login?user=1"

    # Record second hit with bare domain and trailing slash
    off2 = db_instance.record_offender_hit(
        entity_type="url",
        entity_value="sbi-kyc-update.xyz/",
        risk_score=90.0,
        report_id="rep-2",
        category="phishing",
        snippet="urgent kyc link",
        raw_value="sbi-kyc-update.xyz/"
    )
    # Must be the SAME entity with hit_count=2
    assert off2["entity_value"] == "sbi-kyc-update.xyz"
    assert off2["hit_count"] == 2
    assert off2["peak_risk"] == 90.0
    assert len(off2["timeline"]) == 2
    assert off2["timeline"][0]["example_url"] == "http://sbi-kyc-update.xyz/login?user=1"
    assert off2["timeline"][1]["example_url"] == "sbi-kyc-update.xyz/"

def test_migration_merges_existing_duplicate_offenders():
    session = db_instance.get_session()
    try:
        session.query(OffenderModel).filter(OffenderModel.entity_value.in_(["legacy-bank.xyz", "http://legacy-bank.xyz", "www.legacy-bank.xyz/"])).delete(synchronize_session=False)
        session.commit()

        # Manually create 2 legacy unnormalized rows
        row1 = OffenderModel(
            entity_type="url",
            entity_value="http://legacy-bank.xyz",
            hit_count=3,
            peak_risk=75.0,
            avg_risk=70.0,
            first_seen="2026-11-01T10:00:00Z",
            last_seen="2026-11-02T10:00:00Z",
            categories=["phishing"],
            related_reports=["r1", "r2"],
            timeline=[{"timestamp": "2026-11-01T10:00:00Z", "risk_score": 75.0, "raw_value": "http://legacy-bank.xyz"}]
        )
        row2 = OffenderModel(
            entity_type="url",
            entity_value="www.legacy-bank.xyz/",
            hit_count=2,
            peak_risk=85.0,
            avg_risk=80.0,
            first_seen="2026-11-03T10:00:00Z",
            last_seen="2026-11-04T10:00:00Z",
            categories=["scam"],
            related_reports=["r3"],
            timeline=[{"timestamp": "2026-11-03T10:00:00Z", "risk_score": 85.0, "raw_value": "www.legacy-bank.xyz/"}]
        )
        session.add(row1)
        session.add(row2)
        session.commit()
    finally:
        session.close()

    # Run migration
    db_instance.migrate_normalize_offender_urls()

    # Query merged record
    merged = db_instance.get_offender_by_value("legacy-bank.xyz")
    assert merged is not None
    assert merged["entity_value"] == "legacy-bank.xyz"
    assert merged["hit_count"] == 5 # 3 + 2
    assert merged["peak_risk"] == 85.0
    assert set(merged["categories"]) == {"phishing", "scam"}
    assert set(merged["related_reports"]) == {"r1", "r2", "r3"}
    assert len(merged["timeline"]) == 2
    examples = [t.get("example_url") or t.get("raw_value") for t in merged["timeline"]]
    assert "http://legacy-bank.xyz" in examples
    assert "www.legacy-bank.xyz/" in examples

    # Ensure duplicate unnormalized rows no longer exist
    session2 = db_instance.get_session()
    try:
        dups = session2.query(OffenderModel).filter(OffenderModel.entity_value.in_(["http://legacy-bank.xyz", "www.legacy-bank.xyz/"])).all()
        assert len(dups) == 0, f"Expected 0 duplicates, found {len(dups)}"
    finally:
        session2.close()

