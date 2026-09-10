import re
import os
import requests
import whois  # type: ignore[import-untyped]  # python-whois has no type stubs
import socket
from datetime import datetime
from cachetools import TTLCache, cached

# 10 minute TTL cache for API lookups to avoid rate limits
cache = TTLCache(maxsize=1000, ttl=600)

TARGET_BRANDS = [
    "paypal.com",
    "apple.com",
    "bankofamerica.com",
    "google.com",
    "microsoft.com",
    "amazon.com",
    "netflix.com",
    "facebook.com"
]

URL_SHORTENERS = [
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "ow.ly",
    "buff.ly"
]

SE_INDICATORS = {
    "credential_request": [r"\b(password|login|credentials).*(verify|confirm|reset)\b", r"\b(verify|confirm|reset).*(password|login|credentials)\b", r"\bwhat is your mother's maiden name\b"],
    "otp_code_request": [r"\b(send|give|provide).*(code|otp|one time password)\b", r"\bverify your ssn\b"],
    "account_verification_pressure": [r"\b(verify your account|login to confirm|update your payment)\b"],
    "payment_request": [r"\b(wire me|bank transfer|send money|pay me)\b"],
    "gift_card_request": [r"\b(gift card|apple card|google play card)\b"],
    "crypto_payment_request": [r"\b(send|transfer).*(btc|bitcoin|eth|ethereum|crypto)\b"],
    "ransom_demand": [r"\b(pay me|send bitcoin to|ransom|transfer funds immediately)\b", r"\b(if you don't pay)\b"],
    "blackmail_indicator": [r"\b(i have your photos|pay me or i will leak|expose you|send me money or)\b", r"\b(release the video)\b", r"(leak|expose).*(photos|pictures|images|nudes)", r"(photos|pictures|images|nudes).*(will be|are going to be) (leaked|exposed|sent)"],
    "investment_scam_indicator": [r"\b(crypto|bitcoin|investment opportunity|ponzi|pyramid scheme)\b", r"\b(guaranteed returns)\b"]
}

URGENCY_PATTERNS = [
    r"\burgent\b",
    r"\bimmediately\b",
    r"\bact now\b",
    r"\bexpires\b",
    r"\blast chance\b",
    r"\bwithin 24 hours\b",
    r"\brespond immediately\b",
    r"\bdon't delay\b"
]

IMPERSONATION_BRANDS = ["Microsoft", "Google", "Apple", "Amazon", "PayPal"]
IMPERSONATION_KEYWORDS = ["Support", "Security", "Team", "Service", "Admin", "Administrator", "Customer Service"]

DANGEROUS_SCHEME_PATTERN = re.compile(r'\b(javascript|data):[^\s]+', re.IGNORECASE)

def is_ip_based(domain):
    pattern = re.compile(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?::[0-9]+)?$')
    return bool(pattern.match(domain))

def is_url_shortener(domain):
    for shortener in URL_SHORTENERS:
        if domain == shortener or domain.endswith("." + shortener):
            return True
    return False

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def extract_urls(text):
    # Basic URL extraction regex
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = url_pattern.findall(text)
    return list(set(urls))

def extract_emails(text):
    email_pattern = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    emails = email_pattern.findall(text)
    return list(set(emails))

def get_domain(url):
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""

@cached(cache)
def check_safe_browsing(url):
    api_key = os.environ.get("GOOGLE_SAFE_BROWSING_API_KEY")
    if not api_key:
        return None
    
    endpoint = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}"
    payload = {
        "client": {
            "clientId": "shieldai",
            "clientVersion": "1.0.0"
        },
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [
                {"url": url}
            ]
        }
    }
    
    try:
        # Timeout 4 seconds
        response = requests.post(endpoint, json=payload, timeout=4.0)
        if response.status_code == 200:
            data = response.json()
            if "matches" in data and len(data["matches"]) > 0:
                # Return the actual threatType so the caller can route the boost
                threat_type = data["matches"][0].get("threatType", "UNKNOWN")
                return threat_type  # e.g. "SOCIAL_ENGINEERING", "MALWARE", "UNWANTED_SOFTWARE"
            return "safe"
        return None
    except Exception as e:
        print(f"Safe Browsing check failed: {e}")
        return None

import concurrent.futures

@cached(cache)
def check_domain_age(domain):
    try:
        def fetch_whois():
            # socket timeout helps if python-whois uses sockets directly
            socket.setdefaulttimeout(4.0)
            try:
                return whois.whois(domain)
            finally:
                socket.setdefaulttimeout(None)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fetch_whois)
            w = future.result(timeout=4.0)
            
        creation_date = w.creation_date
        
        if isinstance(creation_date, list):
            creation_date = creation_date[0]
            
        if creation_date:
            if creation_date.tzinfo is not None:
                creation_date = creation_date.replace(tzinfo=None)
            age = (datetime.now() - creation_date).days
            return age
        return None
    except concurrent.futures.TimeoutError:
        print(f"WHOIS check timed out for {domain}")
        return None
    except Exception as e:
        print(f"WHOIS check failed for {domain}: {e}")
        return None

def check_typosquatting(domain):
    if not domain:
        return None
        
    for brand in TARGET_BRANDS:
        # Avoid penalizing the exact brand
        if domain == brand:
            continue
            
        # Calculate edit distance
        dist = levenshtein_distance(domain, brand)
        if dist == 1 or dist == 2:  # Typosquat
            return brand
    return None

@cached(cache)
def check_hibp_breaches(email):
    api_key = os.environ.get("HIBP_API_KEY")
    if not api_key:
        return None
        
    endpoint = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
    headers = {
        "hibp-api-key": api_key,
        "user-agent": "ShieldAI-Detection-Engine"
    }
    try:
        response = requests.get(endpoint, headers=headers, timeout=4.0)
        if response.status_code == 200:
            breaches = response.json()
            return len(breaches)
        elif response.status_code == 404:
            return 0
        return None
    except Exception as e:
        print(f"HIBP check failed: {e}")
        return None

def analyze_text_for_threat_intel(text):
    urls = extract_urls(text)
    emails = extract_emails(text)
    
    intel = {
        "urls": [],
        "emails": [],
        "malicious_urls": [],
        "threat_signals": {
            "url_shorteners": [],
            "ip_based_urls": [],
            "dangerous_schemes": [],
            "social_engineering": {
                "detected": False,
                "indicators": []
            },
            "urgency": {
                "detected": False,
                "count": 0,
                "indicators": []
            },
            "brand_impersonation": {
                "detected": False,
                "brands": []
            }
        }
    }
    
    text_lower = text.lower()
    
    # Check Social Engineering Indicators
    for ind_name, patterns in SE_INDICATORS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                if ind_name not in intel["threat_signals"]["social_engineering"]["indicators"]:
                    intel["threat_signals"]["social_engineering"]["indicators"].append(ind_name)
                    intel["threat_signals"]["social_engineering"]["detected"] = True
                
    # Check Urgency
    urgency_matches = set()
    for pattern in URGENCY_PATTERNS:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            # We normalize the matched text as indicator name (e.g. "act now" -> "act_now")
            indicator = match.group(0).replace(" ", "_").replace("'", "")
            urgency_matches.add(indicator)
            
    if urgency_matches:
        intel["threat_signals"]["urgency"]["detected"] = True
        intel["threat_signals"]["urgency"]["indicators"] = list(urgency_matches)
        intel["threat_signals"]["urgency"]["count"] = len(urgency_matches)
        
    # Check Brand Impersonation
    for brand in IMPERSONATION_BRANDS:
        for kw in IMPERSONATION_KEYWORDS:
            if re.search(rf"\b{brand.lower()}\s+{kw.lower()}\b", text_lower):
                if brand not in intel["threat_signals"]["brand_impersonation"]["brands"]:
                    intel["threat_signals"]["brand_impersonation"]["brands"].append(brand)
                    intel["threat_signals"]["brand_impersonation"]["detected"] = True
                    
    # Check Dangerous Schemes
    for match in DANGEROUS_SCHEME_PATTERN.finditer(text):
        scheme = match.group(1).lower()
        # To avoid adding the same scheme multiple times
        if not any(d["scheme"] == scheme for d in intel["threat_signals"]["dangerous_schemes"]):
            intel["threat_signals"]["dangerous_schemes"].append({
                "scheme": scheme,
                "status": "suspicious"
            })
    
    for url in urls:
        domain = get_domain(url)
        url_intel = {
            "url": url,
            "domain": domain
        }
        
        sb_status = check_safe_browsing(url)
        age = check_domain_age(domain)
        squat = check_typosquatting(domain)
        
        if sb_status:
            url_intel["safe_browsing"] = sb_status
        if age is not None:
            url_intel["domain_age_days"] = age
        if squat:
            url_intel["typosquat_match"] = squat
            
        is_ip = is_ip_based(domain)
        is_shortener = is_url_shortener(domain)
        
        if is_ip:
            url_intel["ip_based_url"] = True
            intel["threat_signals"]["ip_based_urls"].append({
                "url": url,
                "reason": "An IP-based URL was detected instead of a conventional domain name."
            })
            
        if is_shortener:
            url_intel["url_shortener"] = True
            intel["threat_signals"]["url_shorteners"].append({
                "url": url,
                "reason": "A URL shortener was detected; the final destination is not visible in the submitted URL."
            })
            
        intel["urls"].append(url_intel)
        
        # Build malicious_url structure
        m_url = {
            "url": url,
            "domain": domain,
            "status": "Safe",
            "risk_score": 0,
            "reason": "Verified Clean"
        }
        
        is_high_risk = False
        
        # Check Typosquatting first
        if squat:
            m_url["status"] = "High Risk"
            m_url["risk_score"] = 85
            m_url["reason"] = f"Typosquatting of {squat}"
            is_high_risk = True
            
        # Check Safe Browsing (overrides typosquatting if more severe)
        if sb_status and sb_status != "safe":
            m_url["status"] = "High Risk"
            m_url["risk_score"] = 90
            m_url["reason"] = f"Google Safe Browsing ({sb_status})"
            is_high_risk = True
            
        if not is_high_risk:
            if sb_status == "safe":
                if age is not None:
                    if age < 30:
                        m_url["status"] = "Suspicious"
                        m_url["risk_score"] = 40
                        m_url["reason"] = f"Suspiciously New Domain ({age} days old)"
                    else:
                        m_url["status"] = "Safe"
                        m_url["risk_score"] = 0
                        m_url["reason"] = "Verified Clean"
                else:
                    # Safe Browsing clean, but WHOIS failed/timeout -> Unknown
                    m_url["status"] = "Unknown"
                    m_url["risk_score"] = 25
                    m_url["reason"] = "Verification Failed / Timed Out"
            else:
                # Safe Browsing failed/timeout (sb_status is None)
                m_url["status"] = "Unknown"
                m_url["risk_score"] = 25
                m_url["reason"] = "Verification Failed / Timed Out"

        intel["malicious_urls"].append(m_url)
        
    for email in emails:
        email_intel = {
            "email": email
        }
        
        breach_count = check_hibp_breaches(email)
        if breach_count is not None:
            email_intel["breach_count"] = breach_count
            
        intel["emails"].append(email_intel)
        
    return intel

# Cycle 2: PII Detection and Masking

AADHAAR_REGEX = re.compile(r'\b[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?[0-9]{4}\b')
PAN_REGEX = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')
PHONE_REGEX = re.compile(r'(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})|\b\d{3}[-.\s]?\d{4}\b')
EMAIL_REGEX = re.compile(r'\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b')

def extract_pii(text: str) -> list:
    """Returns a list of detected PII categories."""
    if not text or not isinstance(text, str):
        return []
    
    categories = []
    
    # Check Aadhaar first
    aadhaar_matches = AADHAAR_REGEX.findall(text)
    if aadhaar_matches:
        categories.append("Aadhaar")
        
    # Check PAN
    if PAN_REGEX.search(text):
        categories.append("PAN")
        
    # Check Phone - if Aadhaar matches overlap, we need to be careful not to count phone separately
    # But for extraction, we can just do a simple search. Wait, if it's just Aadhaar, we don't want to falsely flag as Phone too.
    # It's better to mask Aadhaar first and then check for Phone.
    text_masked_aadhaar = AADHAAR_REGEX.sub("[AADHAAR REDACTED]", text)
    if PHONE_REGEX.search(text_masked_aadhaar):
        categories.append("Phone")
        
    # Check Email
    if EMAIL_REGEX.search(text):
        categories.append("Email")
        
    return categories

def mask_pii(text: str) -> str:
    """Masks Aadhaar, PAN, and Indian phone numbers in the text."""
    if not text or not isinstance(text, str):
        return text
        
    # 1. Mask Aadhaar FIRST to prevent overlapping Phone regex matches
    text = AADHAAR_REGEX.sub("[AADHAAR REDACTED]", text)
    
    # 2. Mask PAN
    text = PAN_REGEX.sub("[PAN REDACTED]", text)
    
    # 3. Mask Phone
    text = PHONE_REGEX.sub("[PHONE REDACTED]", text)
    
    # 4. Mask Email
    text = EMAIL_REGEX.sub("[EMAIL REDACTED]", text)
    
    return text
