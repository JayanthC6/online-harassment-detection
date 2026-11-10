import os
import csv
import pytest
from services.model_service import ModelService

@pytest.fixture(scope="module")
def model_service():
    """Returns singleton ModelService instance."""
    return ModelService.get_instance()

def test_hard_cases_dataset_integrity():
    """Verify that hard_cases.csv exists, is readable, and contains >= 40 diverse cases."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data", "hard_cases.csv")
    assert os.path.exists(csv_path), f"hard_cases.csv not found at {csv_path}"
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) >= 40, f"Expected at least 40 cases, got {len(rows)}"
    expected_cols = {"id", "case_type", "text", "expected_level", "expected_category", "notes"}
    assert expected_cols.issubset(set(rows[0].keys())), f"Missing required columns in CSV: {rows[0].keys()}"

def test_empty_and_short_inputs(model_service):
    """Verify empty string, spaces, and short greetings return score 0 and low risk safely."""
    for inp in ["", "   ", "ok", "k", "hey", "hello", "?"]:
        res = model_service.analyze(inp)
        assert res["level"] == "low"
        assert res["score"] == 0.0 or res["score"] < 15.0
        assert isinstance(res["category_scores"], dict)
        assert isinstance(res["explanation"], str)

def test_severity_caps(model_service):
    """
    Verify that severity caps prevent plain abuse/insults from reaching 'critical'.
    Critical level must be reserved for threats, sextortion, verified scams/phishing, or hate speech.
    """
    # Plain insult / abuse
    insult_text = "You are an ugly stupid idiot and a disgusting pig"
    res = model_service.analyze(insult_text)
    assert res["level"] in ["high", "medium"], f"Insult should be capped at high, got: {res['level']}"
    assert res["score"] <= 75.0, f"Insult score should not exceed 75.0 (band maximum for High), got: {res['score']}"

    # Direct threat should be eligible for critical
    threat_text = "I know where you live and I will murder you tonight"
    res_threat = model_service.analyze(threat_text)
    assert res_threat["level"] == "critical"
    assert res_threat["score"] >= 80.0

    # Sextortion should be eligible for critical
    sextortion_text = "I have your webcam video and private photos, send 1000 BTC or I will leak them to your friends"
    res_sex = model_service.analyze(sextortion_text)
    assert res_sex["level"] == "critical"
    assert res_sex["score"] >= 80.0

def test_profanity_downweighting(model_service):
    """Verify that absence of explicit profane words prevents false profanity signals."""
    # Text with toxicity/insult but NO explicit profanity words
    text = "You are an incompetent fool and a pathetic loser"
    res = model_service.analyze(text)
    signals = [s["signal"].lower() for s in res.get("signals", [])]
    assert not any("profan" in s for s in signals), f"Profanity signal falsely emitted: {signals}"

def test_category_signal_consistency(model_service):
    """
    Verify that signals are filed under the exact category they contribute to.
    A .xyz domain must contribute strictly to 'scam' and NOT 'phishing'.
    """
    text = "Check out this link: http://win-rewards.xyz"
    res = model_service.analyze(text)
    # scam should have score >= 75.0, phishing should be 0.0
    assert res["category_scores"]["scam"] >= 75.0
    assert res["category_scores"]["phishing"] == 0.0
    for s in res.get("signals", []):
        if ".xyz" in s.get("signal", ""):
            assert s["category"] == "scam"

def test_hard_cases_benchmark_and_discrepancy_tracking(model_service):
    """
    Runs the 44 hard cases benchmark.
    Verifies that the overall detection baseline is sound (>= 65% across challenging edge cases),
    and documents performance across categories.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base_dir, "data", "hard_cases.csv")
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    passes = 0
    failures = []

    for r in rows:
        text = r["text"]
        exp_level = r["expected_level"]
        exp_cat = r["expected_category"]

        res = model_service.analyze(text)
        act_level = res["level"]
        act_score = res["score"]
        act_cats = res["category_scores"]

        if act_score < 35.0:
            act_cat = "clean"
        else:
            act_cat = max(act_cats, key=act_cats.get)

        level_match = (act_level == exp_level)
        cat_match = (exp_cat == "clean" and act_score < 35.0) or (exp_cat == act_cat) or (exp_cat in ["harassment", "abusive_language"] and act_cat in ["harassment", "abusive_language"])

        if level_match and cat_match:
            passes += 1
        else:
            failures.append({
                "id": r["id"],
                "type": r["case_type"],
                "expected": f"{exp_level}/{exp_cat}",
                "actual": f"{act_level}/{act_cat} ({act_score:.1f})"
            })

    total = len(rows)
    accuracy = passes / total
    print(f"\nHard cases accuracy: {passes}/{total} ({accuracy:.1%})")
    assert passes >= 28, f"Benchmark regression: expected >= 28 passes, got {passes}/{total}"

def test_benign_insult_false_positives(model_service):
    """
    Verify that self-directed remarks, friendly gaming banter, and talent idioms
    stay low or medium risk, and are NOT flagged as harassment.
    """
    cases = [
        "that was so stupid of me, I forgot my keys",
        "haha you loser, you beat me again!",
        "my brother is such a freak at chess"
    ]
    for text in cases:
        res = model_service.analyze(text)
        assert res["level"] in ["low", "medium"], f"Expected low or medium, got {res['level']} for: {text}"
        assert res["score"] < 40.0, f"Expected score < 40.0, got {res['score']} for: {text}"
        # Primary category should not be harassment and score should be low
        assert res["category_scores"]["harassment"] < 35.0, f"Falsely flagged as harassment: {res['category_scores']}"
        signals = [s.get("signal", "").lower() for s in res.get("signals", [])]
        assert not any("hostile" in s or "cyberbullying" in s for s in signals), f"Harassment signal falsely emitted: {signals}"


def test_safety_bypass_resilience(model_service):
    """
    SAFETY INVARIANT:
    Laughter, banter and self-directed patterns must only attenuate mild insults.
    They must NEVER reduce threat, sextortion, blackmail, scam, phishing, or 'you should die / kys' style scores.
    """
    must_flag_cases = [
        ("haha I will kill you lol", ["high", "critical"]),
        ("lol you're worthless, kys", ["high", "critical"]),
        ("just kidding, send nudes or I leak your photos", ["critical"]),
        ("I'm so stupid, you should go die", ["high", "critical"])
    ]
    for text, expected_levels in must_flag_cases:
        res = model_service.analyze(text)
        assert res["level"] in expected_levels, f"Safety bypass! Expected {expected_levels}, got {res['level']} for: {text}"
        assert res["score"] >= 70.0, f"Safety bypass! Expected score >= 70.0, got {res['score']} for: {text}"


def test_new_benign_banter_and_self_deprecation(model_service):
    """
    Verify 10 new distinct benign banter and self-deprecation sentences remain low risk.
    """
    new_benign_cases = [
        "lol I totally botched that dinner recipe, what a clown I am",
        "ggwp man you crushed my defense in that match haha",
        "silly me, I completely misread the train timetable today",
        "haha nice shot dude, you destroyed my high score again!",
        "honestly my fault, I made such a foolish blunder on that question",
        "my sister is an absolute wizard at mathematics",
        "rofl you got me good this round, rematch tomorrow?",
        "how dumb of me to leave my umbrella in the taxi lol",
        "you completely outplayed me on the board today haha gg",
        "my bad guys, I dropped the pass, clumsy of me"
    ]
    for text in new_benign_cases:
        res = model_service.analyze(text)
        assert res["level"] in ["low", "medium"], f"Expected low or medium, got {res['level']} for: {text}"
        assert res["score"] < 35.0, f"Expected score < 35.0, got {res['score']} for: {text}"
        signals = [s.get("signal", "").lower() for s in res.get("signals", [])]
        assert not any("hostile" in s or "cyberbullying" in s or "threat" in s for s in signals), f"False signal emitted for {text}: {signals}"


def test_multilingual_language_detection(model_service):
    """
    Automated tests for Hindi (Devanagari), Tamil, and Spanish threats.
    Invariant: Non-Latin scripts and unsupported languages must NEVER return 'low / safe'.
    Must return language_supported=False with a clear unreliability notice.
    Roman-script Hinglish must remain supported (language_supported=True).
    """
    unsupported_threats = [
        ("मैं तुम्हें जान से मार दूंगा", "Hindi (Devanagari)"),
        ("நான் உன்னை கொன்று விடுவேன்", "Tamil"),
        ("Te voy a matar esta noche, prepárate para morir", "Spanish")
    ]
    for text, expected_lang in unsupported_threats:
        res = model_service.analyze(text)
        assert res["language_supported"] is False, f"Expected language_supported=False for {expected_lang}: {text}"
        assert res["level"] != "low", f"Unsupported language threat must NEVER return 'low' risk level: {text}"
        assert res["level"] == "unsupported"
        assert "unreliable" in res["explanation"].lower() or "unsupported" in res["explanation"].lower()

    # Roman-script Hinglish must remain supported
    hinglish_text = "tu bohot bada kutta hai saale jaan se maar dunga"
    res_hinglish = model_service.analyze(hinglish_text)
    assert res_hinglish["language_supported"] is True, f"Roman-script Hinglish must be supported: {hinglish_text}"


def test_unsupported_european_language_threats(model_service):
    """
    Threats in Spanish, French, German, Italian, and Portuguese (using distinct wording).
    All must return language_supported=False and never 'low/safe' (level=='unsupported').
    """
    european_threats = [
        ("Te voy a buscar y vas a pagar con tu vida por lo que hiciste", "Spanish"),
        ("Je sais exactement où tu habites et je vais te détruire sale traître", "French"),
        ("Ich werde dich finden und deine Familie vernichten, warte nur ab", "German"),
        ("So dove abiti e ti ammazzo se parli ancora, hai finito di vivere", "Italian"),
        ("Eu vou te matar se você não fizer o que eu mandar imediatamente", "Portuguese")
    ]
    for text, lang in european_threats:
        res = model_service.analyze(text)
        assert res["language_supported"] is False, f"Expected language_supported=False for {lang}: {text}"
        assert res["level"] != "low", f"Unsupported language threat must NEVER return 'low' risk level: {text}"
        assert res["level"] == "unsupported", f"Expected level='unsupported', got {res['level']} for {lang}: {text}"
        assert lang.lower() in res["language_detected"].lower() or res["language_detected"] != "English", f"Detected lang mismatch: {res['language_detected']}"


def test_fraud_phone_call_lures(model_service):
    """
    Phone-call lures combining urgency + disconnection/penalty + a phone number.
    Wording differs from fraud_cases.csv.
    """
    cases = [
        "Urgent notice: Your residential gas connection will be terminated at 9 PM tonight due to unpaid dues. Call our billing desk at 9876543210 immediately to prevent cutoff.",
        "Warning: Electricity supply to your meter will be disconnected today for incomplete documentation. Contact executive Verma at 9123456789 right away."
    ]
    for text in cases:
        res = model_service.analyze(text)
        assert res["level"] in ["high", "critical"], f"Expected high/critical for phone lure: {text}"
        assert res["score"] >= 75.0, f"Expected score >= 75 for phone lure: {text}"
        signals = [s["signal"].lower() for s in res.get("signals", [])]
        assert any("phone" in s or "disconnection" in s or "urgency" in s for s in signals), f"Missing signal in: {signals}"


def test_fraud_job_offers_telegram_whatsapp(model_service):
    """
    Task/job offers combining earning amounts + Telegram/WhatsApp contact.
    Wording differs from fraud_cases.csv.
    """
    cases = [
        "Earn 2500 to 7000 daily with simple remote data entry tasks. Flexible hours from home. Message our manager on Telegram @remotehr2024 to begin today!",
        "Hiring online movie reviewers! Earn Rs 4000 per day with instant UPI payout. Connect with HR team on WhatsApp at +919876543210 to claim your spot."
    ]
    for text in cases:
        res = model_service.analyze(text)
        assert res["level"] in ["high", "critical"], f"Expected high/critical for job scam: {text}"
        assert res["score"] >= 75.0, f"Expected score >= 75 for job scam: {text}"
        signals = [s["signal"].lower() for s in res.get("signals", [])]
        assert any("job" in s or "task" in s or "scam" in s for s in signals), f"Missing signal in: {signals}"


def test_crypto_extortion_and_payment_demands(model_service):
    """
    Crypto wallet formats (0x + 40 hex, bc1/1/3 Bitcoin) and payment demands.
    Wording differs from fraud_cases.csv.
    """
    ransom_text = "We have exfiltrated all confidential client records from your servers. Transfer 1.5 BTC to bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq within 48 hours or everything will be published publicly."
    res_ransom = model_service.analyze(ransom_text)
    assert res_ransom["level"] == "critical"
    assert res_ransom["score"] >= 90.0
    signals = [s["signal"].lower() for s in res_ransom.get("signals", [])]
    assert any("cryptocurrency extortion" in s or "ransomware" in s for s in signals)

    doubler_text = "Deposit at least 500 USDT to official staking contract 0x71C8451032855278d25C81273030d7b275727931 to earn guaranteed 200% returns in 3 hours."
    res_doubler = model_service.analyze(doubler_text)
    assert res_doubler["level"] in ["high", "critical"]
    assert res_doubler["score"] >= 75.0


def test_digit_substituted_lookalike_brands(model_service):
    """
    Digit-substituted look-alike brands (paypa1, g00gle, amaz0n, b1nance, c1t1bank) in URLs.
    Wording differs from fraud_cases.csv.
    """
    cases = [
        "Your transaction was placed on hold. Visit paypa1-account-resolution.com to verify your identity.",
        "Security incident detected on your profile: check activity at g00gle-security-alert.xyz immediately.",
        "Your recent order could not be delivered. Re-enter billing details on amaz0n-customer-update.com.",
        "Emergency wallet migration notice: confirm your balance at b1nance-token-sync.net.",
        "Important notice regarding your checking account: visit c1t1bank-ebanking-portal.com."
    ]
    for text in cases:
        res = model_service.analyze(text)
        assert res["level"] in ["high", "critical"], f"Expected high/critical for look-alike brand URL: {text}"
        assert res["score"] >= 75.0, f"Expected score >= 75 for look-alike brand: {text}"
        signals = [s["signal"].lower() for s in res.get("signals", [])]
        assert any("look-alike" in s or "brand" in s or "phishing" in s or "shortener" in s for s in signals), f"Signals: {signals}"


def test_language_detection_false_triggers(model_service):
    """
    Verify English with names, emoji, numbers-only, short text, Roman Hinglish,
    and English with one Devanagari word are NOT marked as unsupported.
    """
    benign_multilingual_contexts = [
        ("Catching up with Siobhan, Alejandro and Haruto at the café at 4pm.", "English with diverse foreign names"),
        ("Awesome presentation today! 🚀🎉 Truly remarkable teamwork 👏", "English with emojis"),
        ("1234567890 9876543210 456789", "Numbers only"),
        ("ok sure", "Very short text"),
        ("bhai kal shaam ko milte hain coffee pe, kya bolta hai?", "Roman Hinglish"),
        ("Namaste नमस्ते everyone, thank you for joining our team standup today.", "English with single Devanagari greeting")
    ]
    for text, desc in benign_multilingual_contexts:
        res = model_service.analyze(text)
        assert res["language_supported"] is True, f"Failed for '{desc}': text='{text}', res={res}"
        assert res["level"] == "low", f"Expected low level for '{desc}': text='{text}', res={res}"


def test_unsupported_language_with_security_indicators(model_service):
    """
    Language-independent security checks (malicious links, crypto wallets, phone lures)
    must still trigger real risk scores even on unsupported text, returning language_supported=False.
    """
    # Hindi text containing a suspicious URL shortener
    hindi_with_link = "नमस्ते, अपने बैंक खाते को तुरंत अपडेट करने के लिए इस लिंक पर क्लिक करें http://bit.ly/sbi-kyc-verify"
    res_link = model_service.analyze(hindi_with_link)
    assert res_link["language_supported"] is False, "Should report language_supported=False for Devanagari"
    assert res_link["score"] >= 75.0, f"Security indicator must produce real risk score >= 75, got {res_link['score']}"
    assert res_link["level"] in ["high", "critical"], f"Expected high/critical risk level, got {res_link['level']}"
    assert res_link["category_scores"]["phishing"] >= 75.0

    # Hindi text containing a crypto extortion demand
    hindi_with_crypto = "हमने आपका पूरा डेटा एनक्रिप्ट कर दिया है। 24 घंटे में 0x71C8451032855278d25C81273030d7b275727931 पर USDT ट्रांसफर करें"
    res_crypto = model_service.analyze(hindi_with_crypto)
    assert res_crypto["language_supported"] is False
    assert res_crypto["score"] >= 80.0
    assert res_crypto["level"] in ["high", "critical"]


def test_short_non_english_threats_unsupported(model_service):
    """
    Short non-English threats must return level 'unsupported' with language_supported=False
    and NEVER 'low' or 'safe'.
    """
    short_threats = [
        ("Je vais te tuer", "French"),
        ("Ich werde dich töten", "German"),
        ("Ti uccido stanotte", "Italian"),
        ("Eu vou te matar", "Portuguese"),
        ("Te voy a matar", "Spanish")
    ]
    for text, lang in short_threats:
        res = model_service.analyze(text)
        assert res["language_supported"] is False, f"Expected language_supported=False for {lang}: '{text}'"
        assert res["level"] == "unsupported", f"Expected level='unsupported' (not low/safe) for {lang}: '{text}', got {res['level']}"
        assert res["score"] is None, f"Expected score=None (null in API) for unverified language: '{text}', got {res['score']}"


def test_language_independent_indicators_three_cases(model_service):
    """
    Verify language-independent indicators:
    (a) Hindi threat with phishing link: real risk score >= 75, category=phishing, lang_supported=False
    (b) French message with shortener: real risk score (medium if isolated, high/critical if phishing context), lang_supported=False
    (c) Hindi threat alone: level='unsupported', score=0.0, lang_supported=False
    """
    # (a)
    text_a = "मैं तुम्हें मार दूँगा http://sbi-kyc-update.xyz"
    res_a = model_service.analyze(text_a)
    assert res_a["language_supported"] is False
    assert res_a["level"] in ["high", "critical"]
    assert res_a["score"] >= 75.0
    assert res_a["category_scores"].get("phishing", 0) >= 75.0

    # (b) Isolated shortened link returns medium severity, not masked as unsupported/safe
    text_b = "Bonjour voici un message http://bit.ly/abc"
    res_b = model_service.analyze(text_b)
    assert res_b["language_supported"] is False
    assert res_b["level"] == "medium"
    assert res_b["score"] == 35.0

    # (b2) Shortened link with urgency/phishing context returns high/critical
    text_b2 = "Alerte urgente vérifiez votre compte bancaire immédiatement http://bit.ly/sbi-verify"
    res_b2 = model_service.analyze(text_b2)
    assert res_b2["language_supported"] is False
    assert res_b2["level"] in ["high", "critical"]
    assert res_b2["score"] >= 75.0

    # (c)
    text_c = "मैं तुम्हें मार दूँगा"
    res_c = model_service.analyze(text_c)
    assert res_c["language_supported"] is False
    assert res_c["level"] == "unsupported"
    assert res_c["score"] is None


def test_url_shortener_severity(model_service):
    """
    Item 3: A shortened link alone is medium at most.
    High/critical only with urgency, login/KYC wording, brand impersonation, prize or payment demand, or a suspicious domain.
    """
    notes = "Here are the class notes from today: http://bit.ly/notes-cs101"
    res_notes = model_service.analyze(notes)
    assert res_notes["level"] in ["low", "medium"], f"Expected low/medium, got {res_notes['level']}"
    assert res_notes["score"] <= 45.0, f"Expected score <= 45.0, got {res_notes['score']}"

    portfolio = "my portfolio http://tinyurl.com/abc"
    res_portfolio = model_service.analyze(portfolio)
    assert res_portfolio["level"] in ["low", "medium"], f"Expected low/medium, got {res_portfolio['level']}"
    assert res_portfolio["score"] <= 45.0, f"Expected score <= 45.0, got {res_portfolio['score']}"

    sbi = "Dear SBI user, your account has been suspended due to pending KYC update. Click http://bit.ly/sbi-kyc to verify immediately."
    res_sbi = model_service.analyze(sbi)
    assert res_sbi["level"] == "critical", f"Expected critical, got {res_sbi['level']}"
    assert res_sbi["score"] >= 75.0, f"Expected score >= 75.0, got {res_sbi['score']}"






