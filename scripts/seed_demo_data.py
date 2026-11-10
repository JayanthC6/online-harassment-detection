"""
ShieldAI — Demo & Testing Data Seeding Script
Populates realistic cyber safety incidents, repeat offenders, chat exports,
and user complaints into the persistent SQLite database (backend/data/shieldai.db).

Usage:
    python scripts/seed_demo_data.py [--force]
"""

import sys
import os
import argparse
from datetime import datetime, timezone, timedelta
import random

# Ensure backend is on PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from core.database import db_instance, ReportModel, OffenderModel, ComplaintModel, ConversationModel
from ml.adapters.threat_intel import mask_pii


DEMO_INCIDENTS = [
    {
        "actor_id": "anon_blackmailer_42",
        "sender": "anon_blackmailer_42",
        "text": "I have recorded intimate video from your webcam. Send 0.15 BTC ($5,000 USD) to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa within 24 hours or I will leak this video to all your Facebook and Instagram contacts.",
        "primary_label": "Sextortion",
        "category": "sextortion",
        "threat_score": 100.0,
        "risk_score": 100.0,
        "confidence": 0.995,
        "severity_tier": "Critical",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 1,
        "status": "open",
        "flagging_reasons": ["Explicit sextortion blackmail pattern detected", "Cryptocurrency ransom demand", "24-hour urgency countdown timer"],
        "threat_intel": {
            "has_threat_intel": True,
            "tactics": ["Sextortion / Webcam extortion bluff", "Social media contact harvesting threat", "Cryptocurrency payment coercion"],
            "financial_indicators": ["0.15 BTC", "$5000 USD"],
            "wallet_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"]
        }
    },
    {
        "actor_id": "raj_phish_sms",
        "sender": "+919876543210",
        "text": "SBI Alert: Dear customer, your YONO account has been suspended due to pending KYC. Click http://sbi-kyc-update.top to update your PAN immediately or your account will be blocked permanently.",
        "primary_label": "Phishing",
        "category": "phishing",
        "threat_score": 96.0,
        "risk_score": 96.0,
        "confidence": 0.982,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 2,
        "status": "reviewing",
        "flagging_reasons": ["Urgent banking suspension lure", "Suspicious low-reputation top-level domain (.top)", "Look-alike brand impersonation: State Bank of India"],
        "threat_intel": {
            "has_threat_intel": True,
            "impersonated_brand": "State Bank of India (SBI)",
            "suspicious_domains": ["sbi-kyc-update.top"],
            "extracted_phones": ["+919876543210"]
        }
    },
    {
        "actor_id": "angry_gamer_99",
        "sender": "angry_gamer_99",
        "text": "I know where you live in Sector 14. I am coming to your house tonight with a knife and I will kill you.",
        "primary_label": "Threat",
        "category": "threat",
        "threat_score": 100.0,
        "risk_score": 100.0,
        "confidence": 0.998,
        "severity_tier": "Critical",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 2,
        "status": "open",
        "flagging_reasons": ["Direct physical violence threat", "Physical stalking / doxxing indicator"],
        "threat_intel": {
            "has_threat_intel": True,
            "tactics": ["Direct threat to bodily safety", "Residential location doxxing"]
        }
    },
    {
        "actor_id": "troll_gang_99",
        "sender": "troll_gang_99",
        "text": "You are completely worthless and pathetic. Nobody here loves you, go drink bleach and die.",
        "primary_label": "Harassment",
        "category": "harassment",
        "threat_score": 94.0,
        "risk_score": 94.0,
        "confidence": 0.965,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 3,
        "status": "resolved",
        "flagging_reasons": ["Severe derogatory harassment", "Encouragement of self-harm"],
        "threat_intel": {
            "has_threat_intel": True,
            "tactics": ["Severe cyberbullying", "Harmful ideation provocation"]
        }
    },
    {
        "actor_id": "crypto_scam_bot",
        "sender": "t.me/crypto_vip_signal",
        "text": "Congratulations! You have been selected for the $50,000 USDT Binance Giveaway. Deposit 0.05 ETH to claim your reward instantly: http://binance-claim-reward.xyz",
        "primary_label": "Scam",
        "category": "scam",
        "threat_score": 88.0,
        "risk_score": 88.0,
        "confidence": 0.941,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 4,
        "status": "open",
        "flagging_reasons": ["Unrealistic financial reward bait", "Crypto advance-fee fraud", "Impersonation of Binance"],
        "threat_intel": {
            "has_threat_intel": True,
            "impersonated_brand": "Binance",
            "suspicious_domains": ["binance-claim-reward.xyz"]
        }
    },
    {
        "actor_id": "stalker_doxx",
        "sender": "shadow_stalker",
        "text": "tere ghar aake marunga kutte, tu bach ke dikha. I have your sister's phone number +919812345678 and home address.",
        "primary_label": "Threat",
        "category": "threat",
        "threat_score": 98.0,
        "risk_score": 98.0,
        "confidence": 0.987,
        "severity_tier": "Critical",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 5,
        "status": "open",
        "flagging_reasons": ["Roman-script Hindi physical threat ('tere ghar aake marunga')", "Family harassment & doxxing threat"],
        "threat_intel": {
            "has_threat_intel": True,
            "tactics": ["Multilingual intimidation", "Third-party family stalking"],
            "extracted_phones": ["+919812345678"]
        }
    },
    {
        "actor_id": "colleague_bob",
        "sender": "colleague_bob",
        "text": "Hey team, the updated sprint deck has been uploaded to Drive. Please review the slides before our 3 PM sync.",
        "primary_label": "Clean",
        "category": "clean",
        "threat_score": 4.0,
        "risk_score": 4.0,
        "confidence": 0.999,
        "severity_tier": "Low",
        "safety_status": "Safe",
        "label": "non_harassing",
        "days_ago": 6,
        "status": "resolved",
        "flagging_reasons": [],
        "threat_intel": {"has_threat_intel": False}
    },
    {
        "actor_id": "anon_blackmailer_42",
        "sender": "anon_blackmailer_42",
        "text": "12 hours left. If you don't transfer the funds to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa your reputation is ruined forever.",
        "primary_label": "Sextortion",
        "category": "sextortion",
        "threat_score": 99.0,
        "risk_score": 99.0,
        "confidence": 0.991,
        "severity_tier": "Critical",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 0,
        "status": "open",
        "flagging_reasons": ["Follow-up extortion pressure", "Active ultimatum countdown"],
        "threat_intel": {
            "has_threat_intel": True,
            "tactics": ["Psychological extortion pressure", "Escalating deadline coercion"]
        }
    }
]

DEMO_OFFENDERS = [
    {
        "entity_type": "sender",
        "entity_value": "anon_blackmailer_42",
        "hit_count": 5,
        "peak_risk": 100.0,
        "avg_risk": 99.2,
        "categories": ["sextortion", "threat"],
        "status": "flagged",
        "notes": "Serial webcam sextortion actor targeting multiple users with bitcoin ransom demands."
    },
    {
        "entity_type": "phone",
        "entity_value": "+919876543210",
        "hit_count": 4,
        "peak_risk": 96.0,
        "avg_risk": 92.5,
        "categories": ["phishing", "scam"],
        "status": "banned",
        "notes": "Originator of mass SBI YONO KYC suspension phishing SMS lures."
    },
    {
        "entity_type": "url",
        "entity_value": "sbi-kyc-update.top",
        "hit_count": 6,
        "peak_risk": 96.0,
        "avg_risk": 94.0,
        "categories": ["phishing"],
        "status": "banned",
        "notes": "Credential harvesting domain mimicking State Bank of India login portal."
    },
    {
        "entity_type": "sender",
        "entity_value": "troll_gang_99",
        "hit_count": 3,
        "peak_risk": 94.0,
        "avg_risk": 89.0,
        "categories": ["harassment"],
        "status": "monitored",
        "notes": "Coordinated harassment account engaging in severe self-harm incitement."
    }
]

DEMO_COMPLAINTS = [
    {
        "user_id": "citizen_user_101",
        "text": "I received threatening WhatsApp messages from phone +919876543210 claiming they have photos of me and demanding money. Please help.",
        "category": "sextortion",
        "threat_score": 95.0,
        "severity_tier": "Critical",
        "status": "reviewing",
        "days_ago": 2
    },
    {
        "user_id": "student_user_204",
        "text": "An anonymous account shadow_stalker sent me messages saying 'tere ghar aake marunga' and knew my sister's phone number +919812345678.",
        "category": "threat",
        "threat_score": 98.0,
        "severity_tier": "Critical",
        "status": "open",
        "days_ago": 1
    },
    {
        "user_id": "citizen_user_305",
        "text": "Phishing SMS claiming my SBI bank account was blocked if I did not enter my Aadhaar 9999 8888 7777 on sbi-kyc-update.top.",
        "category": "phishing",
        "threat_score": 92.0,
        "severity_tier": "High",
        "status": "resolved",
        "days_ago": 4
    }
]


def seed(force: bool = False):
    print("=" * 70)
    print(">>> [SHIELDAI] Seeding Demo & Incident Data into SQLite Persistence")
    print("=" * 70)

    stats = db_instance.get_stats()
    existing_reports = stats.get("total_reports", 0)

    if existing_reports > 0 and not force:
        print(f"[*] Database already contains {existing_reports} reports. Skipping seed (pass --force to re-seed).")
        return

    now = datetime.now(timezone.utc)
    seeded_report_ids = []

    # 1. Seed Incidents
    print(f"\n[1/4] Inserting {len(DEMO_INCIDENTS)} realistic threat & harassment incident reports...")
    for inc in DEMO_INCIDENTS:
        created_time = now - timedelta(days=inc["days_ago"], hours=random.randint(1, 10))
        raw_text = inc["text"]
        masked_text = mask_pii(raw_text)

        report_data = {
            "text": masked_text,
            "text_preview": masked_text[:140],
            "text_full": masked_text,
            "primary_label": inc["primary_label"],
            "category": inc["category"],
            "threat_score": inc["threat_score"],
            "risk_score": inc["risk_score"],
            "confidence": inc["confidence"],
            "severity_tier": inc["severity_tier"],
            "safety_status": inc["safety_status"],
            "label": inc["label"],
            "actor_id": inc["actor_id"],
            "sender": inc["sender"],
            "source": "demo_seed",
            "status": inc["status"],
            "user_id": "demo_user",
            "flagging_reasons": inc["flagging_reasons"],
            "secondary_labels": {inc["category"]: inc["risk_score"] / 100.0},
            "threat_intel": inc.get("threat_intel", {}),
            "evidence": [{"quote": masked_text[:80], "reason": inc["flagging_reasons"][0] if inc["flagging_reasons"] else "Baseline"}],
            "created_at": created_time,
            "logged_at": created_time.isoformat()
        }

        report_id = db_instance.log_message(report_data)
        seeded_report_ids.append(report_id)
        print(f"  + [{inc['severity_tier'].upper():<8}] {inc['category']:<26} | Actor: {inc['actor_id']}")

    # 2. Seed Repeat Offenders
    print(f"\n[2/4] Registering {len(DEMO_OFFENDERS)} repeat offender threat actors...")
    for off in DEMO_OFFENDERS:
        for i in range(off["hit_count"]):
            hit_time = (now - timedelta(days=i + 1)).isoformat()
            db_instance.record_offender_hit(
                entity_type=off["entity_type"],
                entity_value=off["entity_value"],
                risk_score=off["peak_risk"] - (i * 2.0),
                report_id=seeded_report_ids[0] if seeded_report_ids else None,
                category=off["categories"][0],
                snippet=f"Observed malicious {off['categories'][0]} activity indicator"
            )
        print(f"  + [{off['entity_type'].upper():<6}] {off['entity_value']:<28} | Hits: {off['hit_count']} | Peak: {off['peak_risk']}%")

    # 3. Seed Complaints
    print(f"\n[3/4] Registering {len(DEMO_COMPLAINTS)} citizen complaints with PII masking...")
    for comp in DEMO_COMPLAINTS:
        comp_time = now - timedelta(days=comp["days_ago"])
        masked_comp_text = mask_pii(comp["text"])
        complaint_data = {
            "user_id": comp["user_id"],
            "text": masked_comp_text,
            "category": comp["category"],
            "threat_score": comp["threat_score"],
            "severity_tier": comp["severity_tier"],
            "status": comp["status"],
            "created_at": comp_time,
            "logged_at": comp_time.isoformat()
        }
        db_instance.add_complaint(complaint_data)
        print(f"  + [{comp['severity_tier'].upper():<8}] Complaint from {comp['user_id']:<18} | Category: {comp['category']}")

    # 4. Verify Final Database Counts
    new_stats = db_instance.get_stats()
    print("\n[4/4] SQLite Database Status Verified:")
    print(f"  * Total Stored Reports:     {new_stats.get('total_reports', 0)}")
    print(f"  * Total Flagged Incidents:  {new_stats.get('total_flagged', 0)}")
    print(f"  * Tracked Repeat Offenders: {len(db_instance.get_offenders())}")
    print(f"  * Stored Complaints:        {len(db_instance.get_complaints())}")
    print("=" * 70)
    print(">>> [SHIELDAI] Demo Data Seeding Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed ShieldAI with demo threat incidents and offender analytics.")
    parser.add_argument("--force", action="store_true", help="Force re-seeding even if database already has records")
    args = parser.parse_args()
    seed(force=args.force)
