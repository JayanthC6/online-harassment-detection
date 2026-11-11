"""
Single canonical storage layer for ShieldAI using SQLAlchemy with SQLite (or PostgreSQL).
All reports, profiles, complaints, audit logs, and users persist across server restarts.
"""
import os
import json
import uuid
from datetime import datetime, timezone, timedelta
from collections import Counter
import math

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, DateTime, JSON,
    desc, asc, or_, and_, func
)
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from core.logger import logger

try:
    from ml.adapters.threat_intel import mask_pii
except Exception:
    def mask_pii(t):
        return t

# ── Canonical Taxonomy & Normalization ───────────────────────────────────────
CANONICAL_CATEGORIES = [
    "clean", "harassment", "threat", "sextortion",
    "phishing", "scam", "abusive_language", "unsupported"
]

CATEGORY_NORMALIZATION_MAP = {
    "clean": "clean",
    "none": "clean",
    "safe": "clean",
    "harassment": "harassment",
    "cyberbullying": "harassment",
    "cyberbullying_harassment": "harassment",
    "cyberbullying / harassment": "harassment",
    "threat": "threat",
    "physical_threat": "threat",
    "threat / stalking": "threat",
    "sextortion": "sextortion",
    "blackmail": "sextortion",
    "extortion": "sextortion",
    "extortion / blackmail": "sextortion",
    "phishing": "phishing",
    "credential_phishing": "phishing",
    "phishing / cybercrime": "phishing",
    "scam": "scam",
    "fraud": "scam",
    "abusive_language": "abusive_language",
    "offensive_language": "abusive_language",
    "abusive": "abusive_language",
    "hate_speech": "abusive_language",
    "hate speech": "abusive_language",
    "toxicity": "abusive_language",
    "toxicity / offensive language": "abusive_language",
    "profanity": "abusive_language",
    "unsupported": "unsupported",
    "unsupported_language": "unsupported",
    "unsupported language": "unsupported"
}

def normalize_category(cat: str) -> str:
    """Normalize any raw category, label, or legacy alias to the canonical set."""
    if not cat:
        return "clean"
    key = str(cat).strip().lower()
    return CATEGORY_NORMALIZATION_MAP.get(key, key if key in CANONICAL_CATEGORIES else "harassment")

Base = declarative_base()


class ReportModel(Base):
    __tablename__ = "reports"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    text = Column(Text, nullable=True)
    text_preview = Column(String(256), nullable=True)
    text_full = Column(Text, nullable=True)
    primary_label = Column(String(64), nullable=True)
    category = Column(String(64), nullable=True)
    threat_score = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    severity_tier = Column(String(32), default="Low")
    safety_status = Column(String(32), default="Safe")
    label = Column(String(32), default="non_harassing")
    actor_id = Column(String(128), index=True, default="Anonymous")
    sender = Column(String(128), nullable=True)
    source = Column(String(32), default="platform")
    status = Column(String(32), default="open")  # open, reviewing, resolved, dismissed
    user_id = Column(String(128), index=True, nullable=True)
    flagging_reasons = Column(JSON, default=list)
    secondary_labels = Column(JSON, default=dict)
    threat_intel = Column(JSON, default=dict)
    guidance = Column(JSON, default=dict)
    evidence = Column(JSON, default=list)
    evidence_plan = Column(JSON, default=dict)
    model_used = Column(String(128), nullable=True)
    logged_at = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "_id": self.id,
            "id": self.id,
            "text": self.text,
            "text_preview": self.text_preview or (self.text[:120] if self.text else ""),
            "text_full": self.text_full or self.text,
            "primary_label": self.primary_label,
            "category": self.category,
            "threat_score": self.threat_score,
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "severity_tier": self.severity_tier,
            "safety_status": self.safety_status,
            "label": self.label,
            "actor_id": self.actor_id,
            "sender": self.sender or self.actor_id,
            "source": self.source,
            "status": self.status,
            "user_id": self.user_id,
            "flagging_reasons": self.flagging_reasons or [],
            "secondary_labels": self.secondary_labels or {},
            "threat_intel": self.threat_intel or {},
            "guidance": self.guidance or {},
            "evidence": self.evidence or [],
            "evidence_plan": self.evidence_plan or {},
            "model_used": self.model_used,
            "which_layer": (self.threat_intel or {}).get("which_layer") if isinstance(self.threat_intel, dict) else ("rules" if (self.model_used and "rules" in self.model_used.lower()) else None),
            "logged_at": self.logged_at or (self.created_at.isoformat() if self.created_at else ""),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ProfileModel(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor_id = Column(String(128), unique=True, index=True, nullable=False)
    first_seen = Column(String(64), nullable=True)
    last_seen = Column(String(64), nullable=True)
    total_reports = Column(Integer, default=0)
    safe_messages = Column(Integer, default=0)
    harmful_messages = Column(Integer, default=0)
    highest_risk = Column(Float, default=0.0)
    avg_risk = Column(Float, default=0.0)
    multi_label_distribution = Column(JSON, default=dict)
    behavior_score = Column(Float, default=0.0)
    behavior_level = Column(String(32), default="Safe")
    recommendation = Column(Text, default="Safe / No action required")
    explanation = Column(JSON, default=list)
    timeline = Column(JSON, default=list)
    status = Column(String(32), default="active")

    def to_dict(self):
        return {
            "actor_id": self.actor_id,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "total_reports": self.total_reports,
            "safe_messages": self.safe_messages,
            "harmful_messages": self.harmful_messages,
            "highest_risk": self.highest_risk,
            "avg_risk": self.avg_risk,
            "multi_label_distribution": self.multi_label_distribution or {},
            "behavior_score": self.behavior_score,
            "behavior_level": self.behavior_level,
            "recommendation": self.recommendation,
            "explanation": self.explanation or [],
            "timeline": self.timeline or [],
            "status": self.status
        }


class OffenderModel(Base):
    __tablename__ = "offenders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(32), index=True, nullable=False)  # "sender", "url", "phone", "email"
    entity_value = Column(String(256), unique=True, index=True, nullable=False)
    hit_count = Column(Integer, default=1)
    peak_risk = Column(Float, default=0.0)
    avg_risk = Column(Float, default=0.0)
    first_seen = Column(String(64), nullable=True)
    last_seen = Column(String(64), nullable=True)
    categories = Column(JSON, default=list)  # list of string categories
    related_reports = Column(JSON, default=list)  # list of report_id strings
    status = Column(String(32), default="active")  # active, flagged, banned, monitored
    timeline = Column(JSON, default=list)  # list of {timestamp, risk_score, report_id, snippet}
    notes = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_value": self.entity_value,
            "hit_count": self.hit_count,
            "peak_risk": round(float(self.peak_risk or 0.0), 1),
            "avg_risk": round(float(self.avg_risk or 0.0), 1),
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "categories": self.categories or [],
            "related_reports": self.related_reports or [],
            "status": self.status,
            "timeline": self.timeline or [],
            "notes": self.notes or ""
        }


class ComplaintModel(Base):
    __tablename__ = "complaints"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(128), index=True, default="anonymous")
    text = Column(Text, nullable=True)
    category = Column(String(64), default="General")
    threat_score = Column(Float, default=0.0)
    severity_tier = Column(String(32), default="Medium")
    status = Column(String(32), default="open")  # open, reviewing, resolved, dismissed
    evidence_file = Column(String(256), nullable=True)
    result_json = Column(JSON, default=dict)
    logged_at = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "_id": self.id,
            "id": self.id,
            "user_id": self.user_id,
            "text": self.text,
            "category": self.category,
            "threat_score": self.threat_score,
            "severity_tier": self.severity_tier,
            "status": self.status,
            "evidence_file": self.evidence_file,
            "result_json": self.result_json or {},
            "logged_at": self.logged_at or (self.created_at.isoformat() if self.created_at else ""),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ConversationModel(Base):
    __tablename__ = "conversations"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    primary_label = Column(String(64), nullable=True)
    severity_tier = Column(String(32), default="Low")
    threat_score = Column(Float, default=0.0)
    conversation_risk = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    escalation_level = Column(String(32), default="Low")
    escalation_score = Column(Float, default=0.0)
    escalation_reason = Column(JSON, default=list)
    messages = Column(JSON, default=list)
    actor_attribution = Column(JSON, default=dict)
    source = Column(String(32), default="platform")
    logged_at = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "_id": self.id,
            "id": self.id,
            "primary_label": self.primary_label,
            "severity_tier": self.severity_tier,
            "threat_score": self.threat_score,
            "conversation_risk": self.conversation_risk or self.threat_score,
            "confidence": self.confidence,
            "escalation_level": self.escalation_level,
            "escalation_score": self.escalation_score,
            "escalation_reason": self.escalation_reason or [],
            "messages": self.messages or [],
            "actor_attribution": self.actor_attribution or {},
            "source": self.source,
            "logged_at": self.logged_at or (self.created_at.isoformat() if self.created_at else ""),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(128), nullable=False)
    user = Column(String(128), default="system")
    details = Column(JSON, default=dict)
    timestamp = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "user": self.user,
            "details": self.details or {},
            "timestamp": self.timestamp or (self.created_at.isoformat() if self.created_at else "")
        }


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), default="User")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String(128), primary_key=True)
    messages = Column(JSON, default=list)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Database:
    """
    Unified SQLite/PostgreSQL Database Manager.
    Replaces both db.py and old core/database.py.
    """
    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._connect()

    def _connect(self):
        # Resolve DB URL
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            sqlite_path = os.environ.get("SQLITE_DB_PATH")
            if not sqlite_path:
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                data_dir = os.path.join(backend_dir, "data")
                os.makedirs(data_dir, exist_ok=True)
                sqlite_path = os.path.join(data_dir, "shieldai.db")
            else:
                if not os.path.isabs(sqlite_path):
                    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    sqlite_path = os.path.join(backend_dir, sqlite_path)
                os.makedirs(os.path.dirname(os.path.abspath(sqlite_path)), exist_ok=True)
            
            db_url = f"sqlite:///{os.path.abspath(sqlite_path)}"

        is_sqlite = db_url.startswith("sqlite")
        connect_args = {"check_same_thread": False} if is_sqlite else {}
        self._engine = create_engine(db_url, connect_args=connect_args, echo=False)
        self._session_factory = scoped_session(sessionmaker(bind=self._engine))

        # Create all tables
        Base.metadata.create_all(self._engine)
        logger.info(f"Connected to persistent database: {db_url}")

        # Seed initial demo data if empty
        self.seed_mock_data_if_empty()

        # Run category migrations on existing rows
        self.run_category_migrations()

        # Run URL entity normalisation migration on existing rows (Item 2)
        self.migrate_normalize_offender_urls()

    def get_session(self):
        return self._session_factory()

    @property
    def is_persistent(self):
        return True

    # ── Reports / Incidents ──────────────────────────────────────────────────

    def log_message(self, entry: dict) -> str:
        session = self.get_session()
        try:
            report_id = entry.get("id") or entry.get("incident_id") or str(uuid.uuid4())
            logged_at = entry.get("logged_at") or datetime.now(timezone.utc).isoformat()
            
            text = entry.get("content") or entry.get("text") or ""
            raw_preview = entry.get("text_preview") or (text[:120] if text else "")
            preview = mask_pii(raw_preview)
            
            raw_cat = entry.get("category") or entry.get("primary_label") or "clean"
            norm_cat = normalize_category(raw_cat)
            prim_label = entry.get("primary_label")
            if not prim_label or prim_label.lower() in CATEGORY_NORMALIZATION_MAP:
                prim_label = norm_cat.replace("_", " ").title()

            report = ReportModel(
                id=str(report_id),
                text=text,
                text_preview=preview,
                text_full=entry.get("text_full") or text,
                primary_label=prim_label,
                category=norm_cat,
                threat_score=float(entry.get("threat_score") or entry.get("risk_score") or 0.0),
                risk_score=float(entry.get("risk_score") or entry.get("threat_score") or 0.0),
                confidence=float(entry.get("confidence") or 0.0),
                severity_tier=entry.get("severity_tier") or entry.get("severity") or "Low",
                safety_status=entry.get("safety_status") or "Safe",
                label=entry.get("label") or "non_harassing",
                actor_id=entry.get("actor_id") or "Anonymous",
                sender=entry.get("sender") or entry.get("actor_id") or "Anonymous",
                source=entry.get("source") or "platform",
                status=entry.get("status") or "open",
                user_id=entry.get("user_id"),
                flagging_reasons=entry.get("flagging_reasons") or [],
                secondary_labels=entry.get("secondary_labels") or {},
                threat_intel=dict(entry.get("threat_intel") or {}, which_layer=entry.get("which_layer") or (entry.get("threat_intel") or {}).get("which_layer")),
                guidance=entry.get("guidance") or {},
                evidence=entry.get("evidence") or [],
                evidence_plan=entry.get("evidence_plan") or {},
                model_used=entry.get("model") or entry.get("model_used"),
                logged_at=logged_at
            )
            session.merge(report)
            session.commit()

            # Automatically index repeat offenders (senders, URLs, phones, emails)
            try:
                from services.offender_service import OffenderService
                OffenderService.track_incident_entities(
                    report_id=report.id,
                    text=report.text,
                    risk_score=report.risk_score,
                    category=report.category,
                    sender=report.sender or report.actor_id
                )
            except Exception as off_err:
                logger.debug(f"Offender tracking note: {off_err}")

            return report.id
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to log message to DB: {e}")
            return str(uuid.uuid4())
        finally:
            session.close()

    def get_reports(self, page=1, page_size=20, sort_by="logged_at", sort_order="desc",
                    search="", category="", risk_level="", source=None, user_id=None):
        session = self.get_session()
        try:
            q = session.query(ReportModel)
            if source:
                q = q.filter(ReportModel.source == source)
            elif source is False:
                q = q.filter(ReportModel.source != "self_serve")
            else:
                q = q.filter(ReportModel.source != "self_serve")

            if user_id:
                q = q.filter(ReportModel.user_id == user_id)
            if category:
                norm_cat = normalize_category(category)
                q = q.filter(func.lower(ReportModel.category) == norm_cat)
            if search:
                term = f"%{search}%"
                q = q.filter(or_(ReportModel.text.ilike(term), ReportModel.text_preview.ilike(term), ReportModel.actor_id.ilike(term)))
            if risk_level:
                if risk_level.lower() == "critical":
                    q = q.filter(ReportModel.severity_tier == "Critical")
                elif risk_level.lower() == "high":
                    q = q.filter(ReportModel.severity_tier.in_(["High", "Critical"]))
                elif risk_level.lower() == "medium":
                    q = q.filter(ReportModel.severity_tier == "Medium")
                elif risk_level.lower() == "low":
                    q = q.filter(ReportModel.severity_tier.in_(["Low", "Safe"]))
                elif risk_level.lower() == "unsupported":
                    q = q.filter(ReportModel.severity_tier == "Unsupported")

            total = q.count()
            total_pages = max(1, math.ceil(total / page_size))

            order_col = getattr(ReportModel, sort_by, ReportModel.logged_at)
            if sort_order.lower() == "asc":
                q = q.order_by(asc(order_col))
            else:
                q = q.order_by(desc(order_col))

            items = q.offset((page - 1) * page_size).limit(page_size).all()
            return {
                "reports": [it.to_dict() for it in items],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        finally:
            session.close()

    def get_incident(self, incident_id):
        session = self.get_session()
        try:
            rep = session.query(ReportModel).filter_by(id=str(incident_id)).first()
            return rep.to_dict() if rep else None
        finally:
            session.close()

    def update_incident(self, incident_id, updates):
        session = self.get_session()
        try:
            rep = session.query(ReportModel).filter_by(id=str(incident_id)).first()
            if not rep:
                return False
            for k, v in updates.items():
                if hasattr(rep, k):
                    setattr(rep, k, v)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating incident: {e}")
            return False
        finally:
            session.close()

    def delete_incident(self, incident_id):
        session = self.get_session()
        try:
            rep = session.query(ReportModel).filter_by(id=str(incident_id)).first()
            if rep:
                session.delete(rep)
                session.commit()
                return True
            return False
        finally:
            session.close()

    # ── Conversations ────────────────────────────────────────────────────────

    def log_conversation(self, entry: dict) -> str:
        session = self.get_session()
        try:
            conv_id = entry.get("id") or str(uuid.uuid4())
            logged_at = entry.get("logged_at") or datetime.now(timezone.utc).isoformat()
            conv = ConversationModel(
                id=str(conv_id),
                primary_label=entry.get("primary_label") or "Mixed",
                severity_tier=entry.get("severity_tier") or "Low",
                threat_score=float(entry.get("threat_score") or entry.get("conversation_risk") or 0.0),
                conversation_risk=float(entry.get("conversation_risk") or entry.get("threat_score") or 0.0),
                confidence=float(entry.get("confidence") or 0.0),
                escalation_level=entry.get("escalation_level") or "Low",
                escalation_score=float(entry.get("escalation_score") or 0.0),
                escalation_reason=entry.get("escalation_reason") or [],
                messages=entry.get("messages") or [],
                actor_attribution=entry.get("actor_attribution") or {},
                source=entry.get("source") or "platform",
                logged_at=logged_at
            )
            session.merge(conv)
            session.commit()

            # Index repeat offenders from flagged conversation messages (Item 1)
            try:
                from services.offender_service import OffenderService
                conv_id = conv.id
                for msg in (conv.messages or []):
                    # Check if message is flagged (+1 hit per flagged message)
                    score = float(msg.get("risk_score") or msg.get("score") or 0.0)
                    pred = msg.get("prediction") or {}
                    prim_cat = (pred.get("primary_label") or pred.get("category") or msg.get("category") or "clean").lower()
                    is_flagged = (
                        msg.get("is_flagged") is True
                        or (score >= 35.0 and prim_cat not in ["clean", "none", "safe"])
                        or (pred.get("label") == "harassing" and score >= 30.0 and prim_cat not in ["clean", "none", "safe"])
                    )
                    if is_flagged:
                        OffenderService.track_incident_entities(
                            report_id=conv_id,
                            text=msg.get("text", ""),
                            risk_score=score or float(conv.threat_score or 0.0),
                            category=prim_cat if prim_cat not in ["clean", "none"] else conv.primary_label,
                            sender=msg.get("sender")
                        )
            except Exception as off_err:
                logger.debug(f"Conversation offender tracking note: {off_err}")

            return conv.id
        finally:
            session.close()

    def get_conversations(self, page=1, page_size=20, sort_by="logged_at", sort_order="desc"):
        session = self.get_session()
        try:
            q = session.query(ConversationModel).filter(ConversationModel.source != "self_serve")
            total = q.count()
            total_pages = max(1, math.ceil(total / page_size))
            order_col = getattr(ConversationModel, sort_by, ConversationModel.logged_at)
            if sort_order.lower() == "asc":
                q = q.order_by(asc(order_col))
            else:
                q = q.order_by(desc(order_col))
            items = q.offset((page - 1) * page_size).limit(page_size).all()
            return {
                "conversations": [it.to_dict() for it in items],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        finally:
            session.close()

    # ── Profiles / Repeat Offenders ──────────────────────────────────────────

    def get_profile(self, actor_id: str) -> dict:
        if not actor_id:
            return None
        session = self.get_session()
        try:
            prof = session.query(ProfileModel).filter_by(actor_id=str(actor_id)).first()
            return prof.to_dict() if prof else None
        finally:
            session.close()

    def save_profile(self, profile: dict):
        if not profile or not profile.get("actor_id"):
            return
        session = self.get_session()
        try:
            prof = session.query(ProfileModel).filter_by(actor_id=str(profile["actor_id"])).first()
            if not prof:
                prof = ProfileModel(actor_id=str(profile["actor_id"]))
                session.add(prof)

            prof.first_seen = profile.get("first_seen")
            prof.last_seen = profile.get("last_seen")
            prof.total_reports = int(profile.get("total_reports", 0))
            prof.safe_messages = int(profile.get("safe_messages", 0))
            prof.harmful_messages = int(profile.get("harmful_messages", 0))
            prof.highest_risk = float(profile.get("highest_risk", 0.0))
            prof.avg_risk = float(profile.get("avg_risk", 0.0))
            prof.multi_label_distribution = profile.get("multi_label_distribution", {})
            prof.behavior_score = float(profile.get("behavior_score", 0.0))
            prof.behavior_level = profile.get("behavior_level", "Safe")
            prof.recommendation = profile.get("recommendation", "")
            prof.explanation = profile.get("explanation", [])
            prof.timeline = profile.get("timeline", [])
            prof.status = profile.get("status", "active")

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving profile: {e}")
        finally:
            session.close()

    def get_all_profiles(self) -> list:
        session = self.get_session()
        try:
            profiles = session.query(ProfileModel).order_by(desc(ProfileModel.behavior_score)).all()
            return [p.to_dict() for p in profiles]
        finally:
            session.close()

    def ban_actor(self, actor_id: str, reason: str = ""):
        session = self.get_session()
        try:
            session.query(ReportModel).filter_by(actor_id=str(actor_id)).update({
                ReportModel.status: "banned"
            })
            prof = session.query(ProfileModel).filter_by(actor_id=str(actor_id)).first()
            if prof:
                prof.status = "banned"
                prof.recommendation = f"Banned: {reason}"
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error banning actor: {e}")
            return False
        finally:
            session.close()

    # ── Repeat Offenders ─────────────────────────────────────────────────────

    def record_offender_hit(self, entity_type: str, entity_value: str, risk_score: float, report_id: str = None, category: str = None, snippet: str = None, raw_value: str = None) -> dict:
        if not entity_value or not str(entity_value).strip():
            return None
        entity_value = str(entity_value).strip()
        raw_example = raw_value or entity_value

        if entity_type == "url":
            from services.offender_service import normalize_url_entity
            entity_value = normalize_url_entity(entity_value)
            if not entity_value:
                return None

        session = self.get_session()
        try:
            offender = session.query(OffenderModel).filter_by(entity_value=entity_value).first()
            now_iso = datetime.now(timezone.utc).isoformat()
            risk_score = float(risk_score or 0.0)
            
            if not offender:
                offender = OffenderModel(
                    entity_type=entity_type,
                    entity_value=entity_value,
                    hit_count=1,
                    peak_risk=risk_score,
                    avg_risk=risk_score,
                    first_seen=now_iso,
                    last_seen=now_iso,
                    categories=[category] if category else [],
                    related_reports=[report_id] if report_id else [],
                    status="flagged" if risk_score >= 70.0 else "active",
                    timeline=[{
                        "timestamp": now_iso,
                        "risk_score": risk_score,
                        "report_id": report_id,
                        "category": category,
                        "snippet": mask_pii(snippet[:120] if snippet else ""),
                        "raw_value": raw_example,
                        "example_url": raw_example if entity_type == "url" else None
                    }]
                )
                session.add(offender)
            else:
                offender.hit_count = (offender.hit_count or 0) + 1
                offender.peak_risk = max(float(offender.peak_risk or 0.0), risk_score)
                total_risk = (float(offender.avg_risk or 0.0) * (offender.hit_count - 1)) + risk_score
                offender.avg_risk = total_risk / offender.hit_count
                offender.last_seen = now_iso
                
                # Update categories
                cats = list(offender.categories or [])
                if category and category not in cats:
                    cats.append(category)
                    offender.categories = cats
                    
                # Update related reports
                reps = list(offender.related_reports or [])
                if report_id and report_id not in reps:
                    reps.append(report_id)
                    offender.related_reports = reps
                    
                # Update timeline
                tl = list(offender.timeline or [])
                tl.append({
                    "timestamp": now_iso,
                    "risk_score": risk_score,
                    "report_id": report_id,
                    "category": category,
                    "snippet": mask_pii(snippet[:120] if snippet else ""),
                    "raw_value": raw_example,
                    "example_url": raw_example if entity_type == "url" else None
                })
                # Keep most recent 50 events in timeline
                offender.timeline = tl[-50:]
                
                if offender.peak_risk >= 70.0 and offender.status == "active":
                    offender.status = "flagged"

            session.commit()
            return offender.to_dict()
        except Exception as e:
            session.rollback()
            logger.error(f"Error recording offender hit: {e}")
            return None
        finally:
            session.close()

    def get_offenders(self, entity_type: str = None, min_risk: float = 0.0, search: str = "", sort_by: str = "hit_count", sort_order: str = "desc", page: int = 1, page_size: int = 50) -> dict:
        session = self.get_session()
        try:
            q = session.query(OffenderModel)
            if entity_type and entity_type.lower() != "all":
                q = q.filter(OffenderModel.entity_type == entity_type.lower())
            if min_risk > 0:
                q = q.filter(OffenderModel.peak_risk >= float(min_risk))
            if search and search.strip():
                q = q.filter(OffenderModel.entity_value.ilike(f"%{search.strip()}%"))

            total = q.count()

            # Sorting
            sort_col = getattr(OffenderModel, sort_by, OffenderModel.hit_count)
            if sort_order == "desc":
                q = q.order_by(desc(sort_col))
            else:
                q = q.order_by(asc(sort_col))

            items = q.offset((page - 1) * page_size).limit(page_size).all()

            # Stats by entity type
            stats_raw = session.query(OffenderModel.entity_type, func.count(OffenderModel.id), func.max(OffenderModel.peak_risk)).group_by(OffenderModel.entity_type).all()
            stats = {
                "total": total,
                "senders": 0,
                "urls": 0,
                "phones": 0,
                "emails": 0,
                "peak_risk_overall": 0.0
            }
            for etype, cnt, max_r in stats_raw:
                if etype == "sender":
                    stats["senders"] = cnt
                elif etype == "url":
                    stats["urls"] = cnt
                elif etype == "phone":
                    stats["phones"] = cnt
                elif etype == "email":
                    stats["emails"] = cnt
                if max_r and max_r > stats["peak_risk_overall"]:
                    stats["peak_risk_overall"] = round(float(max_r), 1)

            return {
                "offenders": [it.to_dict() for it in items],
                "total": total,
                "page": page,
                "page_size": page_size,
                "stats": stats
            }
        finally:
            session.close()

    def get_offender_by_value(self, entity_value: str) -> dict:
        session = self.get_session()
        try:
            val = str(entity_value).strip()
            from services.offender_service import normalize_url_entity
            norm_val = normalize_url_entity(val)
            candidates = [val, f"+{val}", val.lstrip("+")]
            if norm_val:
                candidates.append(norm_val)
            offender = session.query(OffenderModel).filter(
                OffenderModel.entity_value.in_(candidates)
            ).first()
            if not offender:
                return None
            res = offender.to_dict()
            # If related reports exist, fetch minimal preview of each linked report
            linked = []
            for rid in res.get("related_reports", []):
                rep = session.query(ReportModel).filter_by(id=str(rid)).first()
                if rep:
                    linked.append({
                        "id": rep.id,
                        "type": "report",
                        "category": rep.category,
                        "risk_score": rep.risk_score,
                        "severity_tier": rep.severity_tier,
                        "status": rep.status,
                        "text_preview": rep.text_preview,
                        "created_at": rep.created_at.isoformat() if rep.created_at else None
                    })
                else:
                    comp = session.query(ComplaintModel).filter_by(id=str(rid)).first()
                    if comp:
                        linked.append({
                            "id": comp.id,
                            "type": "complaint",
                            "category": comp.category,
                            "risk_score": comp.threat_score,
                            "severity_tier": comp.severity_tier,
                            "status": comp.status,
                            "text_preview": (comp.text[:120] if comp.text else ""),
                            "created_at": comp.created_at.isoformat() if comp.created_at else None
                        })
            res["linked_reports_detail"] = linked
            return res
        finally:
            session.close()

    def update_offender_status(self, entity_value: str, status: str, notes: str = None) -> bool:
        session = self.get_session()
        try:
            offender = session.query(OffenderModel).filter_by(entity_value=entity_value).first()
            if not offender:
                return False
            offender.status = status
            if notes is not None:
                offender.notes = notes
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating offender status: {e}")
            return False
        finally:
            session.close()

    # ── Complaints ───────────────────────────────────────────────────────────

    def add_complaint(self, complaint: dict) -> str:
        session = self.get_session()
        try:
            cid = complaint.get("id") or complaint.get("incident_id") or str(uuid.uuid4())
            logged_at = complaint.get("logged_at") or datetime.now(timezone.utc).isoformat()
            raw_comp_text = complaint.get("text") or ""
            comp = ComplaintModel(
                id=str(cid),
                user_id=complaint.get("user_id") or "anonymous",
                text=mask_pii(raw_comp_text),
                category=complaint.get("category") or "General",
                threat_score=float(complaint.get("threat_score") or complaint.get("risk_score") or 0.0),
                severity_tier=complaint.get("severity_tier") or "Medium",
                status=complaint.get("status") or "open",
                evidence_file=complaint.get("evidence_file"),
                result_json=complaint.get("result") or complaint.get("result_json") or {},
                logged_at=logged_at
            )
            session.merge(comp)
            session.commit()

            # Index repeat offenders from complaint details
            try:
                from services.offender_service import OffenderService
                OffenderService.track_incident_entities(
                    report_id=comp.id,
                    text=comp.text,
                    risk_score=comp.threat_score,
                    category=comp.category,
                    sender=comp.user_id
                )
            except Exception as off_err:
                logger.debug(f"Complaint offender tracking note: {off_err}")

            return comp.id
        finally:
            session.close()

    def get_complaints(self, user_id=None) -> list:
        session = self.get_session()
        try:
            q = session.query(ComplaintModel)
            if user_id:
                q = q.filter_by(user_id=str(user_id))
            items = q.order_by(desc(ComplaintModel.created_at)).all()
            return [it.to_dict() for it in items]
        finally:
            session.close()

    def delete_complaint(self, entry_id, user_id=None) -> bool:
        session = self.get_session()
        try:
            q = session.query(ComplaintModel).filter_by(id=str(entry_id))
            if user_id:
                q = q.filter_by(user_id=str(user_id))
            comp = q.first()
            if comp:
                session.delete(comp)
                session.commit()
                return True
            return False
        finally:
            session.close()

    # ── Users & Auth ─────────────────────────────────────────────────────────

    def create_user(self, username, password_hash, role="User") -> bool:
        session = self.get_session()
        try:
            existing = session.query(UserModel).filter_by(username=username).first()
            if existing:
                return False
            user = UserModel(username=username, password_hash=password_hash, role=role)
            session.add(user)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user {username}: {e}")
            return False
        finally:
            session.close()

    def get_user(self, username) -> dict:
        session = self.get_session()
        try:
            user = session.query(UserModel).filter_by(username=username).first()
            return user.to_dict() if user else None
        finally:
            session.close()

    # ── Audit Log ────────────────────────────────────────────────────────────

    def log_audit_event(self, actor="system", action="unknown", resource=None, detail=None, status="success", error=None, **kwargs):
        session = self.get_session()
        try:
            # Handle callers where user or action was passed as kwargs or positional
            user = kwargs.get("user") or actor or "system"
            act = kwargs.get("action") or action or "unknown"
            merged_details = {}
            if isinstance(detail, dict):
                merged_details.update(detail)
            elif isinstance(kwargs.get("details"), dict):
                merged_details.update(kwargs.get("details"))
            if resource:
                merged_details["resource"] = resource
            if status:
                merged_details["status"] = status
            if error:
                merged_details["error"] = error

            timestamp = datetime.now(timezone.utc).isoformat()
            log = AuditLogModel(action=act, user=user, details=merged_details, timestamp=timestamp)
            session.add(log)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error logging audit event: {e}")
        finally:
            session.close()

    def get_audit_log(self, limit=100) -> list:
        session = self.get_session()
        try:
            logs = session.query(AuditLogModel).order_by(desc(AuditLogModel.id)).limit(limit).all()
            return [l.to_dict() for l in logs]
        finally:
            session.close()

    # ── Chatbot Sessions ─────────────────────────────────────────────────────

    def save_chat_session(self, session_id: str, messages: list):
        session = self.get_session()
        try:
            s = session.query(ChatSessionModel).filter_by(session_id=str(session_id)).first()
            if not s:
                s = ChatSessionModel(session_id=str(session_id), messages=messages)
                session.add(s)
            else:
                s.messages = messages
                s.updated_at = datetime.now(timezone.utc)
            session.commit()
        finally:
            session.close()

    def get_chat_session(self, session_id: str) -> list:
        session = self.get_session()
        try:
            s = session.query(ChatSessionModel).filter_by(session_id=str(session_id)).first()
            return s.messages if s and s.messages else []
        finally:
            session.close()

    # ── Statistics & Analytics ───────────────────────────────────────────────

    def get_stats(self) -> dict:
        session = self.get_session()
        try:
            q = session.query(ReportModel).filter(ReportModel.source != "self_serve")
            total = q.count()
            unsupported = q.filter(or_(
                ReportModel.label == "unsupported",
                ReportModel.category == "unsupported",
                ReportModel.severity_tier == "Unsupported"
            )).count()
            high_risk = q.filter(and_(
                ReportModel.risk_score >= 75,
                ReportModel.category != "unsupported",
                ReportModel.severity_tier != "Unsupported"
            )).count()
            medium_risk = q.filter(and_(
                ReportModel.risk_score >= 40,
                ReportModel.risk_score < 75,
                ReportModel.category != "unsupported",
                ReportModel.severity_tier != "Unsupported"
            )).count()
            safe = q.filter(and_(
                ReportModel.risk_score < 40,
                ReportModel.label != "unsupported",
                ReportModel.category != "unsupported",
                ReportModel.severity_tier != "Unsupported"
            )).count()
            evidence_plans = q.filter(ReportModel.evidence_plan != {}).count()

            # Normalize all categories into the canonical lowercase taxonomy
            categories = [normalize_category(r[0]) for r in q.with_entities(ReportModel.category).all() if r[0]]
            breakdown = dict(Counter(categories))

            all_conf = [r[0] for r in q.with_entities(ReportModel.confidence).all() if r[0] is not None]
            all_risk = [r[0] for r in q.with_entities(ReportModel.risk_score).all() if r[0] is not None]

            avg_conf = sum(all_conf) / len(all_conf) if all_conf else 0.0
            avg_risk = sum(all_risk) / len(all_risk) if all_risk else 0.0

            cq = session.query(ConversationModel).filter(ConversationModel.source != "self_serve")
            conv_total = cq.count()
            conv_escalated = cq.filter(ConversationModel.escalation_score > 0).count()
            conv_risks = [c[0] for c in cq.with_entities(ConversationModel.conversation_risk).all() if c[0] is not None]
            conv_avg_risk = sum(conv_risks) / len(conv_risks) if conv_risks else 0.0

            return {
                "total_flagged": total,
                "total_reports": total,
                "safe_messages": safe,
                "high_risk": high_risk,
                "medium_risk": medium_risk,
                "unsupported": unsupported,
                "evidence_plans_generated": evidence_plans,
                "avg_confidence": round(avg_conf, 3),
                "avg_risk_score": round(avg_risk, 1),
                "category_breakdown": breakdown,
                "conversation_stats": {
                    "total": conv_total,
                    "escalated": conv_escalated,
                    "avg_risk": round(conv_avg_risk, 1)
                }
            }
        finally:
            session.close()

    def get_daily_counts(self, days: int = 30) -> list:
        now = datetime.now(timezone.utc)
        date_counts = {}
        for i in range(days):
            d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            date_counts[d] = 0

        session = self.get_session()
        try:
            cutoff = (now - timedelta(days=days)).isoformat()
            reports = session.query(ReportModel.logged_at).filter(
                ReportModel.source != "self_serve",
                ReportModel.logged_at >= cutoff
            ).all()
            for (logged_at,) in reports:
                if logged_at:
                    date_str = logged_at[:10]
                    if date_str in date_counts:
                        date_counts[date_str] += 1

            return sorted(
                [{"date": k, "count": v} for k, v in date_counts.items()],
                key=lambda x: x["date"]
            )
        finally:
            session.close()

    def get_analytics(self) -> dict:
        stats = self.get_stats()
        return {
            "categories": stats.get("category_breakdown", {}),
            "total": stats.get("total_reports", 0),
            "high_risk": stats.get("high_risk", 0),
            "medium_risk": stats.get("medium_risk", 0),
            "safe": stats.get("safe_messages", 0),
            "unsupported": stats.get("unsupported", 0),
            "risk_distribution": {
                "high": stats.get("high_risk", 0),
                "medium": stats.get("medium_risk", 0),
                "low": stats.get("safe_messages", 0),
                "unsupported": stats.get("unsupported", 0)
            }
        }

    def purge_expired_data(self, retention_days: int = None) -> dict:
        """
        Purges reports, complaints, chat sessions, and audit logs older than the configurable retention period.
        Configured via DATA_RETENTION_DAYS (default: 90 days). If set to 0 or negative, retention purging is disabled.
        """
        if retention_days is None:
            try:
                retention_days = int(os.environ.get("DATA_RETENTION_DAYS", "90"))
            except (ValueError, TypeError):
                retention_days = 90

        if retention_days <= 0:
            return {
                "status": "disabled",
                "retention_days": retention_days,
                "purged_reports": 0,
                "purged_complaints": 0,
                "purged_conversations": 0,
                "purged_chat_sessions": 0,
                "purged_audit_logs": 0
            }

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        session = self.get_session()
        try:
            del_reports = session.query(ReportModel).filter(ReportModel.created_at < cutoff).delete(synchronize_session=False)
            del_complaints = session.query(ComplaintModel).filter(ComplaintModel.created_at < cutoff).delete(synchronize_session=False)
            del_convs = session.query(ConversationModel).filter(ConversationModel.created_at < cutoff).delete(synchronize_session=False)
            del_sessions = session.query(ChatSessionModel).filter(ChatSessionModel.updated_at < cutoff).delete(synchronize_session=False)
            del_audit = session.query(AuditLogModel).filter(AuditLogModel.created_at < cutoff).delete(synchronize_session=False)

            session.commit()
            logger.info(f"Data retention purge completed: {del_reports} reports, {del_complaints} complaints, {del_convs} convs, {del_sessions} sessions, {del_audit} audit logs older than {retention_days} days.")
            return {
                "status": "success",
                "retention_days": retention_days,
                "cutoff": cutoff.isoformat(),
                "purged_reports": del_reports,
                "purged_complaints": del_complaints,
                "purged_conversations": del_convs,
                "purged_chat_sessions": del_sessions,
                "purged_audit_logs": del_audit
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Error during data retention purge: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            session.close()

    # ── Backward Compatibility Property Wrappers ────────────────────────────

    @property
    def fallback_store(self):
        """Allows legacy code accessing fallback_store to view all reports as dicts."""
        return self.get_reports(page=1, page_size=1000, source=None).get("reports", [])

    @property
    def fallback_conversations(self):
        return self.get_conversations(page=1, page_size=1000).get("conversations", [])

    @property
    def fallback_profiles(self):
        return {p["actor_id"]: p for p in self.get_all_profiles()}

    def seed_mock_data_if_empty(self):
        """Populate initial representative demo data if the persistent database is brand new."""
        session = self.get_session()
        try:
            count = session.query(ReportModel).count()
            if count > 0:
                return

            samples = [
                {"text": "I will kill you and your family, I know where you live", "actor_id": "angry_user_99", "category": "threat", "primary_label": "Threat", "risk_score": 95.0, "severity_tier": "Critical", "label": "harassing"},
                {"text": "You are a stupid idiot and nobody likes you", "actor_id": "troll_master", "category": "harassment", "primary_label": "Harassment", "risk_score": 65.0, "severity_tier": "High", "label": "harassing"},
                {"text": "I am going to release those private photos of you if you don't pay me $1000 in Bitcoin", "actor_id": "anon_blackmail", "category": "sextortion", "primary_label": "Sextortion", "risk_score": 92.0, "severity_tier": "Critical", "label": "harassing"},
                {"text": "Your bank account has been suspended. Please click here to verify your identity: http://paypa1-update.xyz", "actor_id": "phisher_bank", "category": "phishing", "primary_label": "Phishing", "risk_score": 88.0, "severity_tier": "Critical", "label": "harassing"},
                {"text": "Congratulations! You won the International Lottery of $1,000,000. Send $200 processing fee to claim.", "actor_id": "lottery_scammer", "category": "scam", "primary_label": "Scam", "risk_score": 82.0, "severity_tier": "High", "label": "harassing"},
                {"text": "Hey, are we still meeting for lunch tomorrow at 12? Let me know!", "actor_id": "friend_alice", "category": "clean", "primary_label": "Clean", "risk_score": 5.0, "severity_tier": "Low", "label": "non_harassing"}
            ]

            now_iso = datetime.now(timezone.utc).isoformat()
            for s in samples:
                rep = ReportModel(
                    id=str(uuid.uuid4()),
                    text=s["text"],
                    text_preview=s["text"][:120],
                    text_full=s["text"],
                    primary_label=s["primary_label"],
                    category=s["category"],
                    threat_score=s["risk_score"],
                    risk_score=s["risk_score"],
                    confidence=0.95 if s["label"] == "harassing" else 0.99,
                    severity_tier=s["severity_tier"],
                    safety_status="Threat Detected" if s["label"] == "harassing" else "Safe",
                    label=s["label"],
                    actor_id=s["actor_id"],
                    sender=s["actor_id"],
                    source="platform",
                    status="open",
                    logged_at=now_iso
                )
                session.add(rep)

            session.commit()
            logger.info("Database auto-seeded with representative demo incidents.")
        except Exception as e:
            session.rollback()
            logger.warning(f"Could not auto-seed database: {e}")
        finally:
            session.close()

    def run_category_migrations(self):
        """Migrate any existing reports and complaints to the canonical lowercase category set."""
        session = self.get_session()
        try:
            reports = session.query(ReportModel).all()
            changed = 0
            for r in reports:
                norm = normalize_category(r.category)
                if r.category != norm:
                    r.category = norm
                    changed += 1
                if r.primary_label:
                    if r.primary_label.lower() in CATEGORY_NORMALIZATION_MAP:
                        r.primary_label = norm.replace("_", " ").title()
            if changed > 0:
                session.commit()
                logger.info(f"Canonical category migration updated {changed} reports in database.")
        except Exception as e:
            session.rollback()
            logger.warning(f"Error during category migration: {e}")
        finally:
            session.close()

    def migrate_normalize_offender_urls(self):
        """
        Entity normalisation migration (Item 2):
        Normalises existing URL/domain offenders (strips scheme, www, trailing slash, lowercases).
        Merges duplicates into a single record with combined hit count, peak risk, weighted avg risk,
        merged categories, related reports, and timeline entries preserving full raw URL examples.
        """
        session = self.get_session()
        try:
            from services.offender_service import normalize_url_entity
            url_offenders = session.query(OffenderModel).filter_by(entity_type="url").all()
            grouped = {}
            for off in url_offenders:
                norm = normalize_url_entity(off.entity_value)
                if not norm:
                    continue
                grouped.setdefault(norm, []).append(off)

            merged_count = 0
            for norm_val, records in grouped.items():
                if len(records) == 1 and records[0].entity_value == norm_val:
                    continue

                # If one of the records already has entity_value == norm_val, pick it as primary
                primary_idx = next((i for i, r in enumerate(records) if r.entity_value == norm_val), 0)
                primary = records[primary_idx]
                duplicates = [r for i, r in enumerate(records) if i != primary_idx]

                total_hits = sum(r.hit_count or 1 for r in records)
                peak_risk = max(float(r.peak_risk or 0.0) for r in records)
                total_risk_sum = sum(float(r.avg_risk or 0.0) * (r.hit_count or 1) for r in records)
                avg_risk = total_risk_sum / total_hits if total_hits > 0 else peak_risk

                cats = set()
                reps = set()
                merged_timeline = []
                for r in records:
                    for c in (r.categories or []):
                        cats.add(c)
                    for rep in (r.related_reports or []):
                        reps.add(rep)
                    for tl in (r.timeline or []):
                        tl_copy = dict(tl)
                        if "raw_value" not in tl_copy:
                            tl_copy["raw_value"] = r.entity_value
                        if "example_url" not in tl_copy:
                            tl_copy["example_url"] = r.entity_value
                        merged_timeline.append(tl_copy)

                first_seens = [r.first_seen for r in records if r.first_seen]
                last_seens = [r.last_seen for r in records if r.last_seen]

                # Delete duplicate records first so SQLite unique constraint is never violated
                for duplicate in duplicates:
                    session.delete(duplicate)
                session.flush()

                primary.entity_value = norm_val
                primary.hit_count = total_hits
                primary.peak_risk = peak_risk
                primary.avg_risk = round(avg_risk, 1)
                primary.categories = sorted(list(cats))
                primary.related_reports = sorted(list(reps))
                primary.timeline = sorted(merged_timeline, key=lambda x: x.get("timestamp", ""))[-50:]
                if first_seens:
                    primary.first_seen = min(first_seens)
                if last_seens:
                    primary.last_seen = max(last_seens)
                if peak_risk >= 70.0 and primary.status == "active":
                    primary.status = "flagged"

                session.flush()
                merged_count += 1

            if merged_count > 0:
                session.commit()
                logger.info(f"URL entity normalisation migration merged {merged_count} groups of duplicate URL entities.")
        except Exception as e:
            session.rollback()
            logger.warning(f"Error during URL offender migration: {e}")
        finally:
            session.close()


# Global persistent database instance
db_instance = Database()
