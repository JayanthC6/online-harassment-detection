"""
ShieldAI — Demo & Testing Data Seeding Script
Populates ~40 realistic cyber safety incidents spanning the last 14 days,
7 repeat offenders with multi-hit timelines, and 3 citizen complaints
into the persistent SQLite database (backend/data/shieldai.db).

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
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from core.database import db_instance, ReportModel, OffenderModel, ComplaintModel, ConversationModel
from ml.adapters.threat_intel import mask_pii


# ── 40 SYNTHETIC INCIDENTS SPANNING 14 DAYS ─────────────────────────────────
# Mixed categories: threat, sextortion, phishing, scam, harassment, abusive_language, clean, unsupported
# Mixed severity tiers: critical, high, medium, low, unsupported
# Mixed statuses: pending, reviewed, escalated, dismissed
# Two unsupported-language reports: Hindi (Devanagari) and French
DEMO_INCIDENTS = [
    # ── SEXTORTION (5) ──
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
        "status": "escalated",
        "flagging_reasons": ["Explicit sextortion blackmail pattern detected", "Cryptocurrency ransom demand", "24-hour urgency countdown timer"],
        "threat_intel": {
            "has_threat_intel": True,
            "tactics": ["Sextortion / Webcam extortion bluff", "Social media contact harvesting threat", "Cryptocurrency payment coercion"],
            "financial_indicators": ["0.15 BTC", "$5000 USD"],
            "wallet_addresses": ["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"]
        }
    },
    {
        "actor_id": "anon_blackmailer_42",
        "sender": "anon_blackmailer_42",
        "text": "Time is running out. Pay $1,000 in USDT to 0x71CBA58B465e0da9b6Ffe31355b2520a3Cd4F439 or your private pictures will be uploaded to a public Dropbox link.",
        "primary_label": "Sextortion",
        "category": "sextortion",
        "threat_score": 96.0,
        "risk_score": 96.0,
        "confidence": 0.988,
        "severity_tier": "Critical",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 3,
        "status": "pending",
        "flagging_reasons": ["Private media leak extortion", "USDT crypto wallet demand"],
        "threat_intel": {
            "has_threat_intel": True,
            "tactics": ["Extortion via unauthorized media release", "Crypto address payment pressure"],
            "wallet_addresses": ["0x71CBA58B465e0da9b6Ffe31355b2520a3Cd4F439"]
        }
    },
    {
        "actor_id": "insta_scammer_x",
        "sender": "insta_scammer_x",
        "text": "Send me 200 dollars via Google Pay right now or I send your personal photos to your entire followers list on Instagram.",
        "primary_label": "Sextortion",
        "category": "sextortion",
        "threat_score": 92.0,
        "risk_score": 92.0,
        "confidence": 0.970,
        "severity_tier": "Critical",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 6,
        "status": "reviewed",
        "flagging_reasons": ["Instagram contact follower extortion", "Direct payment coercion"]
    },
    {
        "actor_id": "telegram_blackmail",
        "sender": "telegram_blackmail",
        "text": "I will share these private chat screenshots with your college dean and family unless you pay 5000 rupees today.",
        "primary_label": "Sextortion",
        "category": "sextortion",
        "threat_score": 88.0,
        "risk_score": 88.0,
        "confidence": 0.955,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 10,
        "status": "reviewed",
        "flagging_reasons": ["Reputational extortion", "Academic/workplace exposure threat"]
    },
    {
        "actor_id": "unknown_extortionist",
        "sender": "+919811223344",
        "text": "Transfer 10,000 INR to UPI id pay@fakeupi immediately or your edited nude images will be posted online.",
        "primary_label": "Sextortion",
        "category": "sextortion",
        "threat_score": 98.0,
        "risk_score": 98.0,
        "confidence": 0.990,
        "severity_tier": "Critical",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 13,
        "status": "escalated",
        "flagging_reasons": ["Non-consensual imagery threat", "UPI payment demand"]
    },

    # ── THREATS (6) ──
    {
        "actor_id": "shadow_stalker_x",
        "sender": "shadow_stalker_x",
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
        "status": "escalated",
        "flagging_reasons": ["Direct physical violence threat", "Physical stalking / doxxing indicator"],
        "threat_intel": {
            "has_threat_intel": True,
            "tactics": ["Direct threat to bodily safety", "Residential location doxxing"]
        }
    },
    {
        "actor_id": "shadow_stalker_x",
        "sender": "shadow_stalker_x",
        "text": "You cannot hide from me. I was watching you outside your office today at 6 PM. Watch your back.",
        "primary_label": "Threat",
        "category": "threat",
        "threat_score": 95.0,
        "risk_score": 95.0,
        "confidence": 0.980,
        "severity_tier": "Critical",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 4,
        "status": "escalated",
        "flagging_reasons": ["Physical stalking surveillance", "Intimidation"]
    },
    {
        "actor_id": "angry_neighbor",
        "sender": "angry_neighbor",
        "text": "Next time I see your car parked there I will smash your head with a baseball bat.",
        "primary_label": "Threat",
        "category": "threat",
        "threat_score": 94.0,
        "risk_score": 94.0,
        "confidence": 0.975,
        "severity_tier": "Critical",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 7,
        "status": "pending",
        "flagging_reasons": ["Specific weapon violence threat"]
    },
    {
        "actor_id": "hinglish_troll",
        "sender": "hinglish_troll",
        "text": "tu mil mujhe bahar tera khoon pi jaunga kutte jaan se maar dunga",
        "primary_label": "Threat",
        "category": "threat",
        "threat_score": 96.0,
        "risk_score": 96.0,
        "confidence": 0.985,
        "severity_tier": "Critical",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 9,
        "status": "reviewed",
        "flagging_reasons": ["Hinglish direct death threat ('jaan se maar dunga')"]
    },
    {
        "actor_id": "discord_toxic_user",
        "sender": "discord_toxic_user",
        "text": "If you don't delete your post I will track your IP and leak your family's home address to 4chan.",
        "primary_label": "Threat",
        "category": "threat",
        "threat_score": 88.0,
        "risk_score": 88.0,
        "confidence": 0.960,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 11,
        "status": "reviewed",
        "flagging_reasons": ["Doxxing threat", "Family safety harassment"]
    },
    {
        "actor_id": "crypto_extorter",
        "sender": "crypto_extorter",
        "text": "Transfer 2 Bitcoin or we will execute a swatting raid on your registered home address.",
        "primary_label": "Threat",
        "category": "threat",
        "threat_score": 92.0,
        "risk_score": 92.0,
        "confidence": 0.970,
        "severity_tier": "Critical",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 14,
        "status": "dismissed",
        "flagging_reasons": ["Swatting violence extortion", "Cryptocurrency coercion"]
    },

    # ── PHISHING (6) ──
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
        "status": "reviewed",
        "flagging_reasons": ["Urgent banking suspension lure", "Suspicious low-reputation top-level domain (.top)", "Look-alike brand impersonation: State Bank of India"],
        "threat_intel": {
            "has_threat_intel": True,
            "impersonated_brand": "State Bank of India (SBI)",
            "suspicious_domains": ["sbi-kyc-update.top"],
            "extracted_phones": ["+919876543210"]
        }
    },
    {
        "actor_id": "raj_phish_sms",
        "sender": "+919876543210",
        "text": "Dear SBI user, mandatory PAN verification required before midnight. Visit http://sbi-kyc-update.top/auth to avoid penalty charges.",
        "primary_label": "Phishing",
        "category": "phishing",
        "threat_score": 95.0,
        "risk_score": 95.0,
        "confidence": 0.980,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 4,
        "status": "escalated",
        "flagging_reasons": ["Urgent banking KYC verify lure", "Suspicious domain"],
        "threat_intel": {
            "has_threat_intel": True,
            "impersonated_brand": "State Bank of India (SBI)",
            "suspicious_domains": ["sbi-kyc-update.top"]
        }
    },
    {
        "actor_id": "hdfc_phish_desk",
        "sender": "+919876500011",
        "text": "HDFC Bank Alert: Your NetBanking access has expired. Please verify your debit card pin at http://hdfc-security-portal.xyz immediately.",
        "primary_label": "Phishing",
        "category": "phishing",
        "threat_score": 94.0,
        "risk_score": 94.0,
        "confidence": 0.975,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 5,
        "status": "pending",
        "flagging_reasons": ["HDFC brand impersonation", "Credential harvest link", "Risky .xyz TLD"]
    },
    {
        "actor_id": "telecom_fraud_desk",
        "sender": "+919876543210",
        "text": "TRAI Notice: Your SIM card will be deactivated in 2 hours due to unverified documentation. Call our customer executive at 9876543210 immediately.",
        "primary_label": "Phishing",
        "category": "phishing",
        "threat_score": 86.0,
        "risk_score": 86.0,
        "confidence": 0.950,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 8,
        "status": "reviewed",
        "flagging_reasons": ["TRAI regulatory authority impersonation", "Urgent disconnection phone lure"]
    },
    {
        "actor_id": "courier_phish",
        "sender": "IndiaPost-Alert",
        "text": "India Post: Your package #IN992384 could not be delivered due to wrong address. Pay Rs 25 update fee at http://indiapost-parcel-reschedule.com",
        "primary_label": "Phishing",
        "category": "phishing",
        "threat_score": 88.0,
        "risk_score": 88.0,
        "confidence": 0.965,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 12,
        "status": "dismissed",
        "flagging_reasons": ["Postal courier delivery fee lure", "Phishing domain"]
    },
    {
        "actor_id": "netflix_phish",
        "sender": "Billing-Update",
        "text": "Your Netflix membership is on hold because your payment failed. Update billing details at http://netflix-billing-renew.info to continue watching.",
        "primary_label": "Phishing",
        "category": "phishing",
        "threat_score": 82.0,
        "risk_score": 82.0,
        "confidence": 0.940,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 14,
        "status": "reviewed",
        "flagging_reasons": ["Netflix brand look-alike", "Card credential harvesting"]
    },

    # ── SCAMS (5) ──
    {
        "actor_id": "electricity_scammer",
        "sender": "+919123456789",
        "text": "Urgent Warning: Your residential electricity power supply will be cut off tonight at 9:30 PM due to unpaid bill of Rs 1,420. Contact officer Verma at 9123456789 immediately to avoid penalty.",
        "primary_label": "Scam",
        "category": "scam",
        "threat_score": 90.0,
        "risk_score": 90.0,
        "confidence": 0.970,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 3,
        "status": "escalated",
        "flagging_reasons": ["Urgent utility disconnection scare lure", "Direct fraudulent phone number contact"],
        "threat_intel": {
            "has_threat_intel": True,
            "tactics": ["Utility bill disconnection scare scam"],
            "extracted_phones": ["+919123456789"]
        }
    },
    {
        "actor_id": "electricity_scammer",
        "sender": "+919123456789",
        "text": "Final reminder: Electricity meter disconnected in 30 minutes. Transfer Rs 850 immediately or call Verma at 9123456789.",
        "primary_label": "Scam",
        "category": "scam",
        "threat_score": 91.0,
        "risk_score": 91.0,
        "confidence": 0.972,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 5,
        "status": "pending",
        "flagging_reasons": ["Utility disconnection deadline", "Phone lure"]
    },
    {
        "actor_id": "job_scam_recruiter",
        "sender": "Global-HR",
        "text": "Work from home part-time: Earn Rs 3,500 to 10,000 per day by rating products on YouTube and Google Maps. Contact HR Priya on Telegram @earndaily_in right now.",
        "primary_label": "Scam",
        "category": "scam",
        "threat_score": 85.0,
        "risk_score": 85.0,
        "confidence": 0.960,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 7,
        "status": "reviewed",
        "flagging_reasons": ["Part-time employment task fraud", "Telegram contact solicitation"]
    },
    {
        "actor_id": "crypto_doubler_bot",
        "sender": "crypto_doubler_bot",
        "text": "Exclusive giveaway: Send 0.1 ETH to our smart contract wallet and receive 0.2 ETH automatically in 10 minutes. Limited time promo.",
        "primary_label": "Scam",
        "category": "scam",
        "threat_score": 84.0,
        "risk_score": 84.0,
        "confidence": 0.950,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 10,
        "status": "dismissed",
        "flagging_reasons": ["Crypto doubling advance-fee fraud", "Smart contract lure"]
    },
    {
        "actor_id": "lottery_scam_center",
        "sender": "+918877665544",
        "text": "Congratulations! Your mobile number won 25,00,000 INR in KBC WhatsApp lucky draw. Pay 4,500 INR processing fee to claim prize.",
        "primary_label": "Scam",
        "category": "scam",
        "threat_score": 92.0,
        "risk_score": 92.0,
        "confidence": 0.978,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 13,
        "status": "reviewed",
        "flagging_reasons": ["KBC Lottery prize advance-fee scam", "Processing fee demand"]
    },

    # ── HARASSMENT (6) ──
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
        "days_ago": 1,
        "status": "escalated",
        "flagging_reasons": ["Severe self-harm incitement ('drink bleach and die')", "Deprecating dehumanization"],
        "threat_intel": {
            "has_threat_intel": True,
            "tactics": ["Severe self-harm encouragement", "Cyberbullying brigade"]
        }
    },
    {
        "actor_id": "troll_gang_99",
        "sender": "troll_gang_99",
        "text": "Stop posting you clown, nobody wants you here. Delete your profile before we make your life miserable.",
        "primary_label": "Harassment",
        "category": "harassment",
        "threat_score": 86.0,
        "risk_score": 86.0,
        "confidence": 0.945,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 3,
        "status": "reviewed",
        "flagging_reasons": ["Targeted harassment brigade", "Intimidation"]
    },
    {
        "actor_id": "stalker_ex",
        "sender": "stalker_ex",
        "text": "Why are you ignoring my 50 calls? I see you are online right now. Answer me or I will come find you.",
        "primary_label": "Harassment",
        "category": "harassment",
        "threat_score": 82.0,
        "risk_score": 82.0,
        "confidence": 0.935,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 6,
        "status": "pending",
        "flagging_reasons": ["Obsessive repeated stalking communication", "Implicit intimidation"]
    },
    {
        "actor_id": "workplace_bully",
        "sender": "workplace_bully",
        "text": "You are completely incompetent. Everyone in the team laughs at how dumb your presentations are.",
        "primary_label": "Harassment",
        "category": "harassment",
        "threat_score": 68.0,
        "risk_score": 68.0,
        "confidence": 0.910,
        "severity_tier": "Medium",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 8,
        "status": "reviewed",
        "flagging_reasons": ["Workplace cyberbullying", "Hostile disparagement"]
    },
    {
        "actor_id": "gamer_toxic_squad",
        "sender": "gamer_toxic_squad",
        "text": "Uninstall the game you trash garbage player, go end your pathetic life.",
        "primary_label": "Harassment",
        "category": "harassment",
        "threat_score": 92.0,
        "risk_score": 92.0,
        "confidence": 0.960,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 11,
        "status": "dismissed",
        "flagging_reasons": ["Gaming toxicity with self-harm incitement"]
    },
    {
        "actor_id": "anonymous_hater",
        "sender": "anonymous_hater",
        "text": "You are an ugly fat pig, look at yourself in the mirror before posting pictures.",
        "primary_label": "Harassment",
        "category": "harassment",
        "threat_score": 75.0,
        "risk_score": 75.0,
        "confidence": 0.920,
        "severity_tier": "High",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 13,
        "status": "reviewed",
        "flagging_reasons": ["Severe body shaming and abusive insults"]
    },

    # ── ABUSIVE LANGUAGE (4) ──
    {
        "actor_id": "toxic_commenter_1",
        "sender": "toxic_commenter_1",
        "text": "Shut your fucking mouth you absolute moron, nobody asked for your stupid opinion.",
        "primary_label": "Abusive Language",
        "category": "abusive_language",
        "threat_score": 62.0,
        "risk_score": 62.0,
        "confidence": 0.915,
        "severity_tier": "Medium",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 2,
        "status": "pending",
        "flagging_reasons": ["Profanity and aggressive hostility"]
    },
    {
        "actor_id": "gamer_rage_404",
        "sender": "gamer_rage_404",
        "text": "What a bunch of dumb assholes on this team, you all suck at this game.",
        "primary_label": "Abusive Language",
        "category": "abusive_language",
        "threat_score": 58.0,
        "risk_score": 58.0,
        "confidence": 0.890,
        "severity_tier": "Medium",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 5,
        "status": "reviewed",
        "flagging_reasons": ["Vulgar profanity and team insults"]
    },
    {
        "actor_id": "forum_flamer",
        "sender": "forum_flamer",
        "text": "Get the hell out of here with your bullshit arguments, you total piece of shit.",
        "primary_label": "Abusive Language",
        "category": "abusive_language",
        "threat_score": 64.0,
        "risk_score": 64.0,
        "confidence": 0.925,
        "severity_tier": "Medium",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 9,
        "status": "dismissed",
        "flagging_reasons": ["Offensive vulgarity directed at user"]
    },
    {
        "actor_id": "hinglish_abuser",
        "sender": "hinglish_abuser",
        "text": "saale kamine kutte bakwas band kar apni",
        "primary_label": "Abusive Language",
        "category": "abusive_language",
        "threat_score": 55.0,
        "risk_score": 55.0,
        "confidence": 0.880,
        "severity_tier": "Medium",
        "safety_status": "Flagged",
        "label": "harassing",
        "days_ago": 12,
        "status": "reviewed",
        "flagging_reasons": ["Hinglish abusive profanity terms"]
    },

    # ── CLEAN / SAFE (6) ──
    {
        "actor_id": "colleague_user_1",
        "sender": "colleague_user_1",
        "text": "Good morning team! The sprint review meeting has been rescheduled to 3 PM today. Please check the agenda doc.",
        "primary_label": "Clean",
        "category": "clean",
        "threat_score": 4.0,
        "risk_score": 4.0,
        "confidence": 0.992,
        "severity_tier": "Low",
        "safety_status": "Safe",
        "label": "non_harassing",
        "days_ago": 1,
        "status": "reviewed",
        "flagging_reasons": []
    },
    {
        "actor_id": "student_peer",
        "sender": "student_peer",
        "text": "Here are the lecture notes from today's computer networks class. Let me know if you want to study together for the midterm.",
        "primary_label": "Clean",
        "category": "clean",
        "threat_score": 3.0,
        "risk_score": 3.0,
        "confidence": 0.995,
        "severity_tier": "Low",
        "safety_status": "Safe",
        "label": "non_harassing",
        "days_ago": 3,
        "status": "reviewed",
        "flagging_reasons": []
    },
    {
        "actor_id": "customer_support",
        "sender": "customer_support",
        "text": "Thank you for reaching out to customer support. Your ticket #48291 has been resolved successfully.",
        "primary_label": "Clean",
        "category": "clean",
        "threat_score": 2.0,
        "risk_score": 2.0,
        "confidence": 0.998,
        "severity_tier": "Low",
        "safety_status": "Safe",
        "label": "non_harassing",
        "days_ago": 6,
        "status": "reviewed",
        "flagging_reasons": []
    },
    {
        "actor_id": "family_chat",
        "sender": "family_chat",
        "text": "Happy birthday! Hope you have a wonderful day ahead with friends and family. Sending our love!",
        "primary_label": "Clean",
        "category": "clean",
        "threat_score": 1.0,
        "risk_score": 1.0,
        "confidence": 0.999,
        "severity_tier": "Low",
        "safety_status": "Safe",
        "label": "non_harassing",
        "days_ago": 8,
        "status": "reviewed",
        "flagging_reasons": []
    },
    {
        "actor_id": "friend_user_5",
        "sender": "friend_user_5",
        "text": "Hey are you free this weekend to grab lunch and watch the new sci-fi movie?",
        "primary_label": "Clean",
        "category": "clean",
        "threat_score": 2.0,
        "risk_score": 2.0,
        "confidence": 0.997,
        "severity_tier": "Low",
        "safety_status": "Safe",
        "label": "non_harassing",
        "days_ago": 11,
        "status": "reviewed",
        "flagging_reasons": []
    },
    {
        "actor_id": "dev_collaborator",
        "sender": "dev_collaborator",
        "text": "I pushed the unit tests for the authentication module to branch feature/auth. Please review the PR when you have time.",
        "primary_label": "Clean",
        "category": "clean",
        "threat_score": 3.0,
        "risk_score": 3.0,
        "confidence": 0.994,
        "severity_tier": "Low",
        "safety_status": "Safe",
        "label": "non_harassing",
        "days_ago": 14,
        "status": "reviewed",
        "flagging_reasons": []
    },

    # ── UNSUPPORTED LANGUAGE (2) ──
    # Item 5: Exactly two unsupported-language reports with null scores in API, basic safety guidance (112, preserve message, cybercrime.gov.in)
    {
        "actor_id": "hindi_threat_actor",
        "sender": "hindi_threat_actor",
        "text": "मैं तुम्हें देख लूँगा तुम बच नहीं सकते",
        "primary_label": "Unsupported Language",
        "category": "unsupported",
        "threat_score": None,
        "risk_score": None,
        "confidence": 0.0,
        "severity_tier": "Unsupported",
        "safety_status": "Unverified",
        "label": "unsupported",
        "days_ago": 4,
        "status": "pending",
        "flagging_reasons": ["Unsupported language/script detected: Hindi. Automated safety cannot be verified."],
        "language_supported": False,
        "language_detected": "Hindi",
        "language_note": "Non-Latin script detected (Hindi). ShieldAI is calibrated for English and Roman-script Hinglish."
    },
    {
        "actor_id": "french_threat_actor",
        "sender": "french_threat_actor",
        "text": "Je sais où tu habites et je vais te détruire",
        "primary_label": "Unsupported Language",
        "category": "unsupported",
        "threat_score": None,
        "risk_score": None,
        "confidence": 0.0,
        "severity_tier": "Unsupported",
        "safety_status": "Unverified",
        "label": "unsupported",
        "days_ago": 9,
        "status": "reviewed",
        "flagging_reasons": ["Unsupported language/script detected: French. Automated safety cannot be verified."],
        "language_supported": False,
        "language_detected": "French",
        "language_note": "Unsupported European language detected (French). ShieldAI is calibrated for English and Roman-script Hinglish."
    }
]

# ── 7 REPEAT OFFENDERS WITH MULTI-DAY TIMELINES ─────────────────────────────
DEMO_OFFENDERS = [
    {
        "entity_type": "sender",
        "entity_value": "anon_blackmailer_42",
        "hit_count": 5,
        "peak_risk": 100.0,
        "avg_risk": 96.5,
        "categories": ["sextortion"],
        "status": "flagged",
        "notes": "Serial webcam sextortion actor targeting multiple victims with bitcoin payment demands."
    },
    {
        "entity_type": "phone",
        "entity_value": "+919876543210",
        "hit_count": 6,
        "peak_risk": 96.0,
        "avg_risk": 92.0,
        "categories": ["phishing", "scam"],
        "status": "banned",
        "notes": "Originator of mass SBI YONO KYC suspension and TRAI SIM deactivation phishing SMS lures."
    },
    {
        "entity_type": "url",
        "entity_value": "sbi-kyc-update.top",
        "hit_count": 8,
        "peak_risk": 96.0,
        "avg_risk": 94.5,
        "categories": ["phishing"],
        "status": "banned",
        "notes": "Credential harvesting domain mimicking State Bank of India login portal."
    },
    {
        "entity_type": "sender",
        "entity_value": "shadow_stalker_x",
        "hit_count": 5,
        "peak_risk": 100.0,
        "avg_risk": 97.0,
        "categories": ["threat"],
        "status": "flagged",
        "notes": "Hostile cyberstalking persona issuing physical violence and residential surveillance threats."
    },
    {
        "entity_type": "phone",
        "entity_value": "+919123456789",
        "hit_count": 4,
        "peak_risk": 91.0,
        "avg_risk": 89.0,
        "categories": ["scam"],
        "status": "monitored",
        "notes": "Electricity power cutoff scare scam targeting residential power consumers."
    },
    {
        "entity_type": "sender",
        "entity_value": "troll_gang_99",
        "hit_count": 4,
        "peak_risk": 94.0,
        "avg_risk": 90.0,
        "categories": ["harassment"],
        "status": "monitored",
        "notes": "Coordinated harassment account engaging in severe self-harm incitement."
    },
    {
        "entity_type": "crypto_wallet",
        "entity_value": "0x71CBA58B465e0da9b6Ffe31355b2520a3Cd4F439",
        "hit_count": 3,
        "peak_risk": 96.0,
        "avg_risk": 93.0,
        "categories": ["sextortion", "scam"],
        "status": "banned",
        "notes": "Ethereum / USDT wallet destination used in media release extortion demands."
    }
]

# ── 3 COMPLAINTS ─────────────────────────────────────────────────────────────
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
        "text": "An anonymous account shadow_stalker_x sent me messages saying they are outside my house and knew my sister's phone number +919812345678.",
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
            "secondary_labels": {inc["category"]: (inc["risk_score"] / 100.0) if inc["risk_score"] is not None else 0.0},
            "threat_intel": inc.get("threat_intel", {}),
            "evidence": [{"quote": masked_text[:80], "reason": inc["flagging_reasons"][0] if inc["flagging_reasons"] else "Baseline"}],
            "language_supported": inc.get("language_supported", True),
            "language_detected": inc.get("language_detected", "English"),
            "language_note": inc.get("language_note", ""),
            "created_at": created_time,
            "logged_at": created_time.isoformat()
        }

        report_id = db_instance.log_message(report_data)
        seeded_report_ids.append(report_id)
        print(f"  + [{inc['severity_tier'].upper():<11}] {inc['category']:<18} | Actor: {inc['actor_id']}")

    # 2. Seed Repeat Offenders
    print(f"\n[2/4] Registering {len(DEMO_OFFENDERS)} repeat offender threat actors...")
    for off in DEMO_OFFENDERS:
        for i in range(off["hit_count"]):
            hit_time = (now - timedelta(days=i * 2 + 1, hours=i * 3)).isoformat()
            db_instance.record_offender_hit(
                entity_type=off["entity_type"],
                entity_value=off["entity_value"],
                risk_score=off["peak_risk"] - (i * 1.5),
                report_id=seeded_report_ids[0] if seeded_report_ids else None,
                category=off["categories"][0],
                snippet=f"Observed malicious {off['categories'][0]} activity indicator ({off['entity_value']})"
            )
        print(f"  + [{off['entity_type'].upper():<13}] {off['entity_value']:<36} | Hits: {off['hit_count']} | Peak: {off['peak_risk']}%")

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
