"""
OffenderService — Entity extraction and repeat-offender tracking for ShieldAI.
Extracts senders, URLs, phone numbers, and email addresses from incident texts
and maintains cross-report hit counts, peak risks, timelines, and linked incidents.
"""
import re
from typing import Dict, List, Any
from core.database import db_instance
from core.logger import logger

# Regex patterns for entity extraction
URL_PATTERN = re.compile(
    r'(?:https?://|www\.)[a-zA-Z0-9.\-_]+(?::\d+)?(?:/[^\s<>"\'`()]*)?',
    re.IGNORECASE
)
DOMAIN_PATTERN = re.compile(
    r'\b[a-zA-Z0-9.-]+\.(?:com|org|net|in|co|xyz|top|live|online|biz|club|tech|app|link|site|info|icu|pw|vip)\b',
    re.IGNORECASE
)
EMAIL_PATTERN = re.compile(
    r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b',
    re.IGNORECASE
)
# Matches 10-digit Indian numbers and standard international formats
PHONE_PATTERN = re.compile(
    r'(?:\+?91[\s-]?)?[6-9]\d{9}\b|(?:\+[1-9]\d{0,2}[\s-]?)?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,5}\b'
)

IGNORED_SENDERS = {
    "anonymous", "unknown", "system", "user", "admin", "moderator",
    "none", "null", "n/a", "me", "you"
}

def normalize_url_entity(val: str) -> str:
    """
    Normalise URLs and domains (Item 2):
    - strip scheme (http://, https://)
    - strip leading www.
    - strip trailing slash
    - lowercase
    """
    if not val or not isinstance(val, str):
        return ""
    v = val.strip().lower()
    v = re.sub(r'^https?://', '', v)
    v = re.sub(r'^www\.', '', v)
    v = v.rstrip('/')
    return v

class OffenderService:
    @staticmethod
    def extract_entities(text: str, sender: str = None) -> Dict[str, Any]:
        """
        Extracts senders, URLs, phone numbers, and email addresses from text and metadata.
        Normalises URL entities and tracks full raw URL examples.
        """
        entities: Dict[str, Any] = {
            "senders": [],
            "urls": [],
            "raw_urls": {},
            "phones": [],
            "emails": []
        }

        # 1. Sender
        if sender and isinstance(sender, str):
            clean_sender = sender.strip()
            if clean_sender.lower() not in IGNORED_SENDERS and len(clean_sender) > 1:
                entities["senders"].append(clean_sender)

        if not text or not isinstance(text, str):
            return entities

        # 2. URLs & Domains (Item 2: Normalised)
        found_urls = {}
        for u in URL_PATTERN.findall(text):
            clean_u = u.strip().rstrip(".,;:)")
            if clean_u:
                norm_u = normalize_url_entity(clean_u)
                if norm_u and norm_u not in found_urls:
                    found_urls[norm_u] = clean_u
        for d in DOMAIN_PATTERN.findall(text):
            clean_d = d.strip()
            if clean_d:
                norm_d = normalize_url_entity(clean_d)
                if norm_d and norm_d not in found_urls:
                    found_urls[norm_d] = clean_d
        entities["urls"] = sorted(list(found_urls.keys()))
        entities["raw_urls"] = found_urls

        # 3. Emails
        found_emails = set()
        for em in EMAIL_PATTERN.findall(text):
            clean_em = em.strip().lower().rstrip(".,;:")
            if clean_em:
                found_emails.add(clean_em)
        entities["emails"] = sorted(list(found_emails))

        # 4. Phone numbers
        found_phones = set()
        for ph in PHONE_PATTERN.findall(text):
            clean_ph = re.sub(r'[\s\-()]', '', ph)
            # Require at least 10 digits
            digits_only = re.sub(r'\D', '', clean_ph)
            if 10 <= len(digits_only) <= 15:
                found_phones.add(clean_ph)
        entities["phones"] = sorted(list(found_phones))

        return entities

    @staticmethod
    def track_incident_entities(
        report_id: str,
        text: str,
        risk_score: float,
        category: str = None,
        sender: str = None
    ) -> List[Dict[str, Any]]:
        """
        Extracts all entities from the text and logs repeat-offender hits in the database.
        Returns list of recorded offender entity summaries.
        """
        entities = OffenderService.extract_entities(text, sender)
        recorded = []

        snippet = (text[:120] if text else "")

        # Record Senders
        for s in entities["senders"]:
            off = db_instance.record_offender_hit(
                entity_type="sender",
                entity_value=s,
                risk_score=risk_score,
                report_id=report_id,
                category=category,
                snippet=snippet
            )
            if off:
                recorded.append(off)

        # Record URLs (Item 2: normalised entity_value, full URL preserved as raw_value)
        raw_urls = entities.get("raw_urls", {})
        for u in entities["urls"]:
            full_example = raw_urls.get(u, u)
            off = db_instance.record_offender_hit(
                entity_type="url",
                entity_value=u,
                risk_score=risk_score,
                report_id=report_id,
                category=category,
                snippet=snippet,
                raw_value=full_example
            )
            if off:
                recorded.append(off)

        # Record Phone numbers
        for p in entities["phones"]:
            off = db_instance.record_offender_hit(
                entity_type="phone",
                entity_value=p,
                risk_score=risk_score,
                report_id=report_id,
                category=category,
                snippet=snippet
            )
            if off:
                recorded.append(off)

        # Record Emails
        for e in entities["emails"]:
            off = db_instance.record_offender_hit(
                entity_type="email",
                entity_value=e,
                risk_score=risk_score,
                report_id=report_id,
                category=category,
                snippet=snippet
            )
            if off:
                recorded.append(off)

        return recorded

    @staticmethod
    def get_offenders(
        entity_type: str = None,
        min_risk: float = 0.0,
        search: str = "",
        sort_by: str = "hit_count",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 50
    ) -> dict:
        return db_instance.get_offenders(
            entity_type=entity_type,
            min_risk=min_risk,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )

    @staticmethod
    def get_offender_by_value(entity_value: str) -> dict:
        return db_instance.get_offender_by_value(entity_value)

    @staticmethod
    def update_offender_status(entity_value: str, status: str, notes: str = None) -> bool:
        return db_instance.update_offender_status(entity_value, status, notes)

