import re
import os
import requests
import whois
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
                return "unsafe"
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
        "emails": []
    }
    
    for url in urls:
        domain = get_domain(url)
        url_intel = {
            "url": url,
            "domain": domain
        }
        
        sb_status = check_safe_browsing(url)
        if sb_status:
            url_intel["safe_browsing"] = sb_status
            
        age = check_domain_age(domain)
        if age is not None:
            url_intel["domain_age_days"] = age
            
        squat = check_typosquatting(domain)
        if squat:
            url_intel["typosquat_match"] = squat
            
        intel["urls"].append(url_intel)
        
    for email in emails:
        email_intel = {
            "email": email
        }
        
        breach_count = check_hibp_breaches(email)
        if breach_count is not None:
            email_intel["breach_count"] = breach_count
            
        intel["emails"].append(email_intel)
        
    return intel
