"""
ShieldAI Detection Engine Service (Phase 2).
Integrates DistilBERT multi-label classifier with calibrated thresholds,
comprehensive rules layer (phishing, scams, sextortion, link analysis),
and hybrid risk scoring with configurable severity caps.
"""
import os
import re
import json
import logging
from urllib.parse import urlparse
from collections import OrderedDict
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger("ShieldAI.ModelService")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# Early pre-initialization of torch runtime libraries on Windows to prevent DLL collision
try:
    import torch
except Exception as _e:
    pass

# Enforce offline operation for HuggingFace transformers in sandbox
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

LABEL_ORDER = [
    "Hate Speech",
    "Cyberbullying / Harassment",
    "Threat",
    "Toxicity / Offensive Language",
    "Profanity",
    "Clean"
]

DEFAULT_THRESHOLDS = {
    "Hate Speech": 0.807612419128418,
    "Cyberbullying / Harassment": 0.8904848694801331,
    "Threat": 0.5331543684005737,
    "Toxicity / Offensive Language": 0.4209566116333008,
    "Profanity": 0.9965969920158386,
    "Clean": 0.6905590891838074
}

# Configurable severity caps: Plain insults/abuse are capped at High band maximum (<75.0)
DEFAULT_SEVERITY_CAPS = {
    "plain_abuse_cap": float(os.environ.get("SHIELDAI_PLAIN_ABUSE_CAP", 74.0)),
    "unverified_scam_cap": float(os.environ.get("SHIELDAI_UNVERIFIED_SCAM_CAP", 70.0)),
    "educational_cap": float(os.environ.get("SHIELDAI_EDUCATIONAL_CAP", 40.0)),
}

# ── Link and Threat Indicators ───────────────────────────────────────────────

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "rb.gy",
    "shorturl.at", "goo.gl", "ow.ly", "tiny.cc", "buff.ly", "v.gd"
}

RISKY_TLDS = {
    ".xyz", ".top", ".click", ".buzz", ".fit", ".work", ".gq", ".tk",
    ".ml", ".cf", ".ga", ".rest", ".icu", ".cam", ".live", ".link",
    ".space", ".online", ".site", ".cc"
}

TARGET_BRANDS = [
    "paypal.com", "apple.com", "google.com", "microsoft.com",
    "amazon.com", "netflix.com", "facebook.com", "instagram.com",
    "whatsapp.com", "telegram.org", "chase.com", "wellsfargo.com",
    "bankofamerica.com", "citibank.com", "binance.com", "coinbase.com",
    "kraken.com", "sbi.co.in", "hdfcbank.com", "icicibank.com",
    "axisbank.com", "paytm.com", "phonepe.com"
]

SE_URGENCY_PATTERNS = [
    r"\b(?:urgent|immediately|action required|act now|within 24 hours|account suspended|account blocked|temporary suspension|permanent block|last chance|final notice|expires today)\b",
    r"\b(?:unauthorized transaction|suspicious login|security alert|fraud alert)\b"
]

SE_OTP_KYC_REQUEST_PATTERNS = [
    r"\b(?:share your otp|enter otp|send the code|provide your code|verify your ssn|verify aadhaar|send aadhaar|pan card|kyc verification|update kyc|kyc expired|link your pan)\b",
    r"\b(?:share bank details|send account details|credit card pin|cvv number)\b"
]

# Legitimate automated OTP dispatch indicators (telling the user NOT to share)
GENUINE_OTP_INDICATORS = [
    r"\b(?:do not share|never share|not share it with anyone|not share this code|valid for \d+ min|is your secret otp|is your one time password)\b",
    r"\b(?:use code \d{4,8}|your otp is \d{4,8}|\b\d{4,8} is your otp)\b"
]

SCAM_LOTTERY_PRIZE_PATTERNS = [
    # Explicit lottery / prize / sweepstakes winning notices
    r"\b(?:you have won|you'?ve won|you won|selected for (?:a |the )?reward|awarded with (?:a )?[\$£₹]?\d+|won (?:a )?(?:cash prize|lottery|jackpot|sweepstakes))\b",
    r"\b(?:lucky draw|international lottery|prize notification|sweepstakes prize)\b",
    # Congratulations ONLY when paired with prize/winning + claim/call/contact action
    r"\b(?:congratulations|congrats)\b.{0,80}\b(?:won|winner|prize|reward|lottery|cash|jackpot|awarded)\b.{0,80}\b(?:claim|call|contact|collect|redeem|send|click|reply)\b",
    r"\b(?:won|winner|prize|reward|lottery|cash|jackpot|awarded)\b.{0,80}\b(?:congratulations|congrats)\b.{0,80}\b(?:claim|call|contact|collect|redeem|send|click|reply)\b",
    # Standalone prize claim lures
    r"\b(?:claim your prize|claim (?:your )?reward|claim (?:your )?cash)\b"
]

# Phone-call lures combining urgency + disconnection/penalty/threat + phone number
PHONE_CALL_EXTORTION_LURES = [
    r"\b(?:disconnected|deactivated|suspended|terminated|cut off)\b.{0,80}\b(?:call|contact|dial)\b.{0,40}\b(?:\+?\d[\d\s-]{8,14}\d)\b",
    r"\b(?:call|contact|dial)\b.{0,40}\b(?:\+?\d[\d\s-]{8,14}\d)\b.{0,80}\b(?:disconnected|deactivated|suspended|terminated|penalty|bill|arrears)\b",
    r"\b(?:electricity|power supply|water supply|gas pipeline|sim card|mobile number|account)\b.{0,80}\b(?:disconnected|terminated|suspended)\b.{0,80}\b(?:call|contact|dial)\b"
]

# Task-based part-time job or work-from-home scam patterns
TASK_JOB_SCAM_PATTERNS = [
    r"\b(?:part[- ]?time|work from home|wfh|online job|remote (?:job|work|data entry)|review task|daily task|earn money)\b.{0,150}\b(?:telegram|whatsapp|wa\.me|t\.me|@\w+)\b",
    r"\b(?:earn|earning|income|payout)\b.{0,60}(?:[\$£₹]|rs\.?|inr)?\s*\d+[\d,]*\s*(?:to\s*[\$£₹]?\s*\d+[\d,]*)?\s*(?:daily|per day|per task|per video|daily payout|every day)\b.{0,150}\b(?:telegram|whatsapp|wa\.me|t\.me|@\w+)\b",
    r"\b(?:telegram|whatsapp)\b.{0,50}(?:@\w+|t\.me/\w+|wa\.me/\w+|\+?\d{10})\b.{0,150}\b(?:job|earn|part[- ]?time|wfh|income|salary|hiring)\b",
    r"\b(?:hiring|vacancy)\b.{0,80}\b(?:earn|salary|payout|rs\.?|inr)\b.{0,150}\b(?:telegram|whatsapp|wa\.me|t\.me)\b"
]

# Cryptocurrency extortion & ransomware payment patterns
CRYPTO_EXTORTION_PATTERNS = [
    r"\b(?:encrypted|locked|ransomware|files encrypted|database encrypted)\b.{0,80}\b(?:transfer|send|pay|deposit)\b.{0,60}\b(?:usdt|tether|btc|bitcoin|eth|ethereum|crypto|wallet)\b",
    r"\b(?:transfer|send|pay|deposit)\b.{0,60}\b(?:\d+[\d,.]*\s*(?:usdt|btc|eth|crypto|bitcoin|usd|dollars?))\b.{0,80}\b(?:within \d+ (?:hours?|hrs?|days?)|or your|or delete|or leak|or destroy)\b",
    r"\b(?:crypto wallet|wallet address|bitcoin address|usdt wallet|btc address)\b.{0,40}(?:0x[a-fA-F0-9]{4,40}|1[a-km-zA-HJ-NP-Z1-9]{15,34}|3[a-km-zA-HJ-NP-Z1-9]{15,34}|bc1[a-z0-9]{15,59})"
]

# Regex covering standard crypto wallet address formats
CRYPTO_WALLET_REGEX = re.compile(
    r'\b(?:'
    r'0x[a-fA-F0-9]{40}|'                         # Ethereum / EVM 40 hex
    r'1[a-km-zA-HJ-NP-Z1-9]{25,34}|'               # Bitcoin Base58 P2PKH (starts with 1)
    r'3[a-km-zA-HJ-NP-Z1-9]{25,34}|'               # Bitcoin Base58 P2SH (starts with 3)
    r'bc1[a-z0-9]{38,59}|'                         # Bitcoin Bech32 Native SegWit
    r'0x[a-fA-F0-9]{3,10}\.{2,4}[a-fA-F0-9]{0,10}' # Elided address in notices
    r')\b'
)

SCAM_PAYMENT_PATTERNS = [
    r"\b(?:gift card|apple gift card|steam card|google play voucher|amazon gift card|pay via gift card)\b",
    r"\b(?:bitcoin|btc|usdt|crypto wallet|wallet address|eth|ethereum|transfer crypto)\b"
]

SCAM_COURIER_DIGITAL_ARREST_PATTERNS = [
    r"\b(?:digital arrest|customs department|narcotics bureau|parcel detained|courier customs|illegal parcel|cbi investigation|police warrant|cyber crime branch|arrest warrant)\b",
    r"\b(?:customs fee|clearance charge|parcel seized)\b"
]

SEXTORTION_PATTERNS = [
    r"\b(?:webcam|intimate|compromising|private)\b.{0,60}\b(?:video|photo|picture|photos|pictures|nudes?|recording)\b",
    r"\b(?:leak|expose|release|publish|share)\b.{0,60}\b(?:video|photo|picture|photos|pictures|nudes?|webcam)\b",
    r"\b(?:video|photo|picture|photos|pictures|nudes?|webcam)\b.{0,60}\b(?:leak|expose|release|share|send to)\b",
    r"\b(?:pay me|send)\b.{0,60}\b(?:btc|bitcoin|crypto|wallet|money|cash|\$|₹)\b.{0,60}\b(?:or i will|or else)\b",
    r"\b(?:or i will|or else)\b.{0,60}\b(?:leak|expose|release|send to|ruin you)\b",
    r"\b(?:recorded|captured|filmed)\b.{0,60}\b(?:webcam|camera|intimate|naked|private)\b",
    r"\b(?:send to (?:all your|your) (?:friends|family|contacts|employer)|leak these photos)\b"
]

THREAT_PATTERNS = [
    r"\b(?:i will kill you|i am going to kill you|i will hunt you down|i know where you live|watch your back|i will murder you|gonna beat you up|put a bullet in you|slit your throat|end your life)\b",
    r"\b(?:swat your house|find and kill you|destroy your family)\b",
    # Hinglish core threats
    r"\b(?:mar dalunga|maar dalunga|jaan se mar|teri jaan le|dekh lunga tujhe|tere ghar aake marunga)\b"
]

# Severe death wishes and suicide encouragement (CAN NEVER BE ATTENUATED)
SEVERE_DEATH_WISH_PATTERNS = [
    r"\b(?:kys|kill your\s*self|go die|should go die|hope you die|you should die|you should go die|hang your\s*self|drink bleach|end your\s*life)\b"
]

# ── Common Roman-Script Hindi / Hinglish Abuse & Threat Patterns (Rules-Only) ──
# Easy to extend: matches common phonetic Roman-script Hindi threats, vulgar insults, and scams.
HINGLISH_THREAT_PATTERNS = [
    r"\b(?:(?:tere\s*ko\s+|tujhe\s+|teri\s+)?jaan\s+se\s+m[a]*r\s*(?:dunga|dungi|dalunga|dalungi|dene|denge))\b",
    r"\b(?:tere\s+ghar\s+aake\s+m[a]*runga|ghar\s+me\s+ghus\s+ke\s+m[a]*runga|tujhe\s+peetunga)\b",
    r"\b(?:tujhe\s+(?:zinda\s+)?nahi\s+chhodunga|tujhe\s+chhodunga\s+nahi|dekh\s+lunga\s+tujhe|tujhe\s+dekh\s+lunga)\b",
    r"\b(?:teri\s+maut\s+aayegi|tujhe\s+khatam\s+kar\s+(?:dunga|denge)|tujhe\s+uda\s+dunga|goli\s+m[a]*r\s+dunga)\b",
    r"\b(?:hath\s+pair\s+tod\s+dunga|gala\s+kaat\s+dunga|chhuri\s+ghop\s+dunga)\b"
]

HINGLISH_ABUSE_PATTERNS = [
    r"\b(?:kutta|kutti|kutte|kutto|kamina|kamine|kameena|kameene)\b",
    r"\b(?:harami|haraami|haramkhor|haraamkhor)\b",
    r"\b(?:chutiya|chutiye|chutye|choothiya)\b",
    r"\b(?:bhadwa|bhadwe|bhadve|randi|raand|suar|suwar)\b",
    r"\b(?:madarchod|bhenchod|behenchod|bsdk|bhosdike|bhosadi)\b",
    r"\b(?:m\.c\.|b\.c\.)\b",
    r"\b(?:gandu|gaandu|chirkut|chapri)\b",
    r"\b(?:saala|saale|sale)\s+(?:kutta|suar|kutte|pagal|kamina|harami)\b"
]

HINGLISH_SCAM_PATTERNS = [
    r"\b(?:account\s+suspend\s+hone\s+wala\s+hai|turant\s+kyc\s+update\s+karein|kyc\s+update\s+warna\s+fine)\b",
    r"\b(?:inaam\s+jeeta\s+hai|lottery\s+lagi\s+hai|itne\s+rupaye\s+transfer\s+karein)\b",
    r"\b(?:paise\s+(?:bhej|de|daal)\s+warna\s+photo\s+(?:leak|viral))\b"
]

# Benign context keywords that neutralize violent words strictly when used as idioms, sports, or gaming banter
BENIGN_VIOLENT_IDIOM_PATTERNS = [
    r"\b(?:in fifa|in cod|in valorant|in pubg|in fortnite|in chess|in the game|gaming|game tonight)\b",
    r"\b(?:killed that presentation|slaying it|drop dead gorgeous|killing this workout|kill time|killed the exam|killed it on stage)\b"
]

# Benign self-directed or self-deprecating remarks (not targeted harassment)
SELF_DIRECTED_PATTERNS = [
    r"\b(?:of me|of myself|on my part|stupid me|foolish of me|silly me|clumsy of me|how stupid of me|how dumb of me)\b",
    r"\bwhat\s+(?:an?\s+)?\w+\s+i\s+(?:am|was)\b",
    r"\b(?:i(?:'m| am| was)\s+(?:so\s+|such\s+a\s+|really\s+)?(?:stupid|dumb|idiot|fool|loser|freak|mess|clown|clumsy))\b",
    r"\b(?:i feel like (?:a\s+)?(?:loser|failure|idiot|fool|scumbag|mess|clown))\b",
    r"\b(?:my bad|i messed up|i forgot|my fault|my blunder)\b",
    r"\bhow\s+(?:stupid|dumb|foolish|silly|clumsy)\s+of\s+me\b"
]

# Benign talent or skill compliment idioms
TALENT_IDIOM_PATTERNS = [
    r"\b(?:freak|beast|monster|demon|wizard|genius|machine|god)\s+at\s+[a-zA-Z]+\b",
    r"\b(?:freak|force)\s+of\s+nature\b"
]

# Friendly banter / playful competition / laughter context
FRIENDLY_BANTER_PATTERNS = [
    r"\b(?:haha|hehe|lol|lmao|rofl)\b.{0,60}\b(?:you beat me|beat me|you won|beat my score|in the game|gg|good game|rematch|next time|nice one)\b",
    r"\b(?:you beat me|beat me|you won|beat my score|in the game|gg|good game)\b.{0,60}\b(?:haha|hehe|lol|lmao|rofl)\b",
    r"\b(?:just kidding|jk|only teasing|all in good fun)\b"
]

# Educational or news advisory indicators
EDUCATIONAL_SCAM_PATTERNS = [
    r"\b(?:rbi warns|police advisory|cyber crime alert|issued an alert|advising citizens|beware of|how to spot|educational notice|safety advisory)\b"
]

HARASSMENT_INSULT_PATTERNS = [
    # Inherently hostile expressions & severe abuse
    r"\b(?:worthless piece of (?:trash|crap|shit)|disgusting pig|piece of trash|waste of (?:space|oxygen))\b",
    r"\b(?:nobody wants you(?:\s+here)?|nobody likes you)\b",
    r"\b(?:kill yourself|kys|drop dead|burn in hell)\b",
    r"\b(?:ugly\s+and\s+stupid|stupid\s+and\s+ugly|ugly\s+freak|stupid\s+idiot|pathetic\s+loser|scumbag)\b",
    # Targeted 2nd-person insults ("you're so ugly and stupid", "you loser", "you idiot")
    r"\b(?:you(?:'re| are|\s+r)?|u(?:'re| r)?|ur)\s+(?:(?:so|such\s+a|a|an|total|complete|real|fucking|very)\s+)*(?:ugly|stupid|idiot|loser|freak|pathetic|scumbag|moron)\b",
    r"\b(?:you|u)\s+(?:ugly|stupid|loser|idiot|freak|scumbag|moron)\b",
    # 3rd-person targeted insults
    r"\b(?:he|she|they|that\s+(?:guy|girl|person))\s+is\s+(?:(?:so|such\s+a|a|an|total)\s+)*(?:ugly|stupid|idiot|loser|pathetic|scumbag)\b",
    # Hinglish insults
    r"\b(?:kutte|kameene|bewakoof|gadhe|chutiye|bhosadike|harami)\b"
]

# Explicit profane words lexicon to verify Profanity predictions
PROFANITY_WORD_PATTERNS = [
    r"\b(?:f+u+c+k+(?:ing|er|ed|s)?|f\*+ck|fuk|fck)\b",
    r"\b(?:s+h+i+t+(?:ty|s)?|sh\*+t|bullshit)\b",
    r"\b(?:b+i+t+c+h+(?:es|ing)?|b\*+tch|b!tch)\b",
    r"\b(?:c+u+n+t+(?:s)?|c\*+nt)\b",
    r"\b(?:a+s+s+h+o+l+e+(?:s)?|a\*\*hole|a\$\$hole|arsehole)\b",
    r"\b(?:bastard|dick|cock|pussy|whore|slut)\b",
    r"\b(?:chutiya|bhenchod|madarchod|gaand|bhosad[a-z]*|harami)\b"
]


def normalize_text(text: str) -> str:
    """
    General text normalization applied before the neural model and rules engine:
    1. Zero-width characters & invisible unicode formatting removal.
    2. Mixed spacing collapse (e.g. 'k i l l' -> 'kill', 'd i e' -> 'die').
    3. Asterisk/symbol obscenity de-masking (e.g. 'f*ck' -> 'fuck', 'b*tch' -> 'bitch').
    4. Leetspeak & symbol substitutions (k!ll/k1ll -> kill, fr33 -> free, c@rd -> card, a$$hole -> asshole).
    5. Consecutive repeated characters collapse (3+ -> 1, e.g. 'fuuuuck' -> 'fuck', 'sooooo' -> 'so').
    """
    if not text or not isinstance(text, str):
        return ""

    # 1. Zero-width characters & invisible unicode formatting
    norm = re.sub(r'[\u200B-\u200D\uFEFF\u200E\u200F\u202A-\u202E\u00AD\u2060]', '', text)

    # 2. Mixed spacing: collapse sequences of single letters separated by spaces (e.g. 'k i l l', 'd i e')
    def collapse_spaced(m):
        return re.sub(r'\s+', '', m.group(0))
    norm = re.sub(r'(?:\b[a-zA-Z]\s+){2,}[a-zA-Z]\b', collapse_spaced, norm)

    # 3. Asterisk obscenity masking (f*ck -> fuck, b*tch -> bitch, sh*t -> shit, c*nt -> cunt, d*ck -> dick)
    norm = re.sub(r'\b([fF])\*+([cC][kK])\b', r'\g<1>u\g<2>', norm)
    norm = re.sub(r'\b([bB])\*+([tT][cC][hH])\b', r'\g<1>i\g<2>', norm)
    norm = re.sub(r'\b([sS][hH])\*+([tT])\b', r'\g<1>i\g<2>', norm)
    norm = re.sub(r'\b([cC])\*+([nN][tT])\b', r'\g<1>u\g<2>', norm)
    norm = re.sub(r'\b([dD])\*+([cC][kK])\b', r'\g<1>i\g<2>', norm)
    norm = re.sub(r'(?<=[a-zA-Z])\*(?=[a-zA-Z])', 'i', norm)

    # 4. Leetspeak & symbol substitutions
    # ! or 1 inside word -> i
    norm = re.sub(r'(?<=[a-zA-Z])[!1]+(?=[a-zA-Z]|\b)', lambda m: 'i' * len(m.group(0)), norm)
    norm = re.sub(r'\b[!1]+(?=[a-zA-Z]{2,})', lambda m: 'i' * len(m.group(0)), norm)
    # 3 inside word -> e (e.g. fr33 -> free, h3ll -> hell)
    norm = re.sub(r'(?<=[a-zA-Z])3+', lambda m: 'e' * len(m.group(0)), norm)
    norm = re.sub(r'\b3+(?=[a-zA-Z]{2,})', lambda m: 'e' * len(m.group(0)), norm)
    # 0 -> o
    norm = re.sub(r'(?<=[a-zA-Z])0+(?=[a-zA-Z]|\b)', lambda m: 'o' * len(m.group(0)), norm)
    # @ or 4 -> a
    norm = re.sub(r'(?<=[a-zA-Z])[@4]+(?=[a-zA-Z]|\b)', lambda m: 'a' * len(m.group(0)), norm)
    norm = re.sub(r'\b[@4]+(?=[a-zA-Z]{2,})', lambda m: 'a' * len(m.group(0)), norm)
    # $ or 5 -> s
    norm = re.sub(r'(?<=[a-zA-Z])[$5]+(?=[a-zA-Z]|\b)', lambda m: 's' * len(m.group(0)), norm)
    norm = re.sub(r'(?<=[a-zA-Z])[$5]+\b', lambda m: 's' * len(m.group(0)), norm)

    # 5. Repeated characters collapse (3+ -> 1, e.g. 'fuuuuck' -> 'fuck', 'kiiiill' -> 'kill', 'faaaake' -> 'fake')
    norm = re.sub(r'([a-zA-Z])\1{2,}', r'\1', norm)

    return norm

# Backward compatibility alias
deobfuscate_text = normalize_text


class ModelService:
    _instance: Optional["ModelService"] = None

    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.thresholds: Dict[str, float] = dict(DEFAULT_THRESHOLDS)
        self.severity_caps: Dict[str, float] = dict(DEFAULT_SEVERITY_CAPS)
        self.device = None
        self.is_loaded = False
        self.cache: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
        self.max_cache_size = 10000

        self._initialize()

    @classmethod
    def get_instance(cls) -> "ModelService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def model_loaded(self) -> bool:
        """Returns True if the DistilBERT neural model is loaded, False if rules-only mode."""
        return self.is_loaded

    def _initialize(self):
        """Loads model and tokenizer once at startup from backend/models/shieldai."""
        model_dir = os.environ.get("SHIELDAI_MODEL_DIR")
        if not model_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            model_dir = os.path.join(base_dir, "models", "shieldai")

        logger.info(f"Checking for ShieldAI DistilBERT model in: {model_dir}")

        if not os.path.isdir(model_dir):
            logger.warning(
                f"Model directory '{model_dir}' not found. "
                "Running in rules-only fallback mode. App continues normally."
            )
            return

        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            # Device selection: strictly CPU as specified
            self.device = torch.device("cpu")

            # Load thresholds if present
            thresh_path = os.path.join(model_dir, "thresholds.json")
            if os.path.exists(thresh_path):
                try:
                    with open(thresh_path, "r", encoding="utf-8") as f:
                        loaded_thresh = json.load(f)
                    self.thresholds.update(loaded_thresh)
                    logger.info(f"Loaded calibrated thresholds: {self.thresholds}")
                except Exception as e:
                    logger.warning(f"Error reading thresholds.json ({e}). Using calibrated defaults.")

            # Load tokenizer and model offline
            self.tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_dir, local_files_only=True)
            self.model.to(self.device)
            self.model.eval()

            # Verify label order against config.json id2label
            id2label = getattr(self.model.config, "id2label", {})
            mismatch = False
            for idx, expected_name in enumerate(LABEL_ORDER):
                actual_name = id2label.get(str(idx), id2label.get(idx))
                if actual_name != expected_name:
                    mismatch = True
                    break

            if mismatch:
                logger.warning(
                    f"Model config id2label {id2label} does not explicitly match standard names. "
                    f"Adopting calibrated ShieldAI taxonomy order (0..5): {LABEL_ORDER}"
                )
            else:
                logger.info(f"Label order verified: {LABEL_ORDER}")

            self.is_loaded = True
            logger.info("ShieldAI DistilBERT Multi-Label Model successfully loaded.")

        except Exception as e:
            logger.warning(
                f"ShieldAI DistilBERT model failed to load from '{model_dir}': {e}. "
                "Continuing in rules-only fallback mode. The app remains fully operational."
            )
            self.model = None
            self.tokenizer = None
            self.is_loaded = False

    # ── Probability to Relative Score Conversion ───────────────────────────────

    def probability_to_relative_score(self, prob: float, threshold: float) -> float:
        """
        Converts probability into a 0-100 score relative to calibrated threshold:
        - At threshold -> 50.0
        - At 1.0 -> 100.0
        - At 0.0 -> 0.0
        """
        prob = max(0.0, min(1.0, float(prob)))
        threshold = max(0.01, min(0.99, float(threshold)))

        if prob <= threshold:
            score = (prob / threshold) * 50.0
        else:
            score = 50.0 + ((prob - threshold) / (1.0 - threshold)) * 50.0

        return max(0.0, min(100.0, round(score, 1)))

    # ── Neural Inference ───────────────────────────────────────────────────────

    def _predict_model_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Batched neural forward pass."""
        if not self.is_loaded or self.model is None or self.tokenizer is None:
            return [{"probs": {}, "scores": {}, "active": False} for _ in texts]

        import torch

        results = []
        try:
            inputs = self.tokenizer(
                texts,
                truncation=True,
                padding=True,
                max_length=256,
                return_tensors="pt"
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                logits = self.model(**inputs).logits
                probs_tensor = torch.sigmoid(logits).cpu().numpy()

            for i in range(len(texts)):
                row_probs = probs_tensor[i]
                probs_map = {}
                scores_map = {}

                for idx, label_name in enumerate(LABEL_ORDER):
                    p = float(row_probs[idx])
                    thresh = self.thresholds.get(label_name, 0.5)
                    rel_score = self.probability_to_relative_score(p, thresh)
                    probs_map[label_name] = round(p, 4)
                    scores_map[label_name] = rel_score

                results.append({
                    "probs": probs_map,
                    "scores": scores_map,
                    "active": True
                })

        except Exception as e:
            logger.error(f"Neural inference error: {e}")
            results = [{"probs": {}, "scores": {}, "active": False} for _ in texts]

        return results

    # ── Link & Threat Rules Layer ──────────────────────────────────────────────

    def _extract_urls(self, text: str) -> List[str]:
        url_pattern = re.compile(
            r'https?://(?:[a-zA-Z0-9$-_@.&+!*(),]|(?:%[0-9a-fA-F]{2}))+|'
            r'(?:www\.[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)|'
            r'\b(?=[a-zA-Z0-9-]*[a-zA-Z])[a-zA-Z0-9-]{2,63}\.(?:com|org|net|io|co|in|info|biz|xyz|top|click|buzz|gq|tk|ml|cf|ga|icu|cam|cc|link|work)\b(?:/[^\s]*)?',
            re.IGNORECASE
        )
        return list(set(url_pattern.findall(text)))

    def _analyze_links(self, text: str) -> List[Dict[str, Any]]:
        """
        Analyzes links and returns specific signals.
        AGGREGATION RULE: Every link signal MUST be tagged with its true destination category:
        - URL shorteners, direct IP, punycode, brand impersonation -> category: 'phishing'
        - Risky TLDs (.xyz, .top, etc.) -> category: 'scam'
        Each signal contributes ONLY to its filed category.
        """
        urls = self._extract_urls(text)
        signals: List[Dict[str, Any]] = []

        for url in urls:
            full_url = url if url.startswith("http") else "http://" + url
            parsed = urlparse(full_url)
            netloc = (parsed.netloc or parsed.path).lower()
            if ":" in netloc:
                netloc = netloc.split(":")[0]

            # 1. URL Shorteners -> Phishing
            for shortener in URL_SHORTENERS:
                if netloc == shortener or netloc.endswith("." + shortener):
                    signals.append({
                        "layer": "rules",
                        "category": "phishing",
                        "signal": f"Suspicious URL shortener detected ({shortener}) hiding actual destination",
                        "score": 82.0
                    })
                    break

            # 2. Raw IP address links -> Phishing
            if re.match(r'^(?:\d{1,3}\.){3}\d{1,3}$', netloc):
                signals.append({
                    "layer": "rules",
                    "category": "phishing",
                    "signal": f"Direct IP address link detected ({netloc}) commonly used in phishing/malware",
                    "score": 90.0
                })

            # 3. Risky TLDs -> Phishing vs Scam (Applied strictly to full domain tokens)
            for tld in RISKY_TLDS:
                tld_clean = tld.lstrip(".")
                if netloc == tld_clean or netloc.endswith("." + tld_clean):
                    is_phish_lure = any(w in (netloc + parsed.path).lower() for w in ["login", "verify", "signin", "account", "secure", "portal", "update", "auth", "banking"])
                    if is_phish_lure:
                        signals.append({
                            "layer": "rules",
                            "category": "phishing",
                            "signal": f"Deceptive phishing link on high-risk domain ending ({tld})",
                            "score": 74.0
                        })
                    else:
                        signals.append({
                            "layer": "rules",
                            "category": "scam",
                            "signal": f"High-risk domain ending ({tld}) frequently used in fraudulent campaigns",
                            "score": 75.0
                        })
                    break

            # 4. Punycode / Look-alike domains -> Phishing
            if "xn--" in netloc:
                signals.append({
                    "layer": "rules",
                    "category": "phishing",
                    "signal": f"Punycode homograph domain detected ({netloc})",
                    "score": 88.0
                })

            # 5. Look-alike brand impersonation in domain (with digit/char substitution canonicalization: 1->l/i, i->l, 0->o, 3->e, 5->s, 8->b) -> Phishing
            variants = [
                netloc.replace("1", "l").replace("0", "o").replace("3", "e").replace("5", "s").replace("8", "b"),
                netloc.replace("1", "i").replace("0", "o").replace("3", "e").replace("5", "s").replace("8", "b"),
                netloc.replace("i", "l").replace("0", "o").replace("3", "e").replace("5", "s").replace("8", "b"),
            ]
            for brand in TARGET_BRANDS:
                brand_base = brand.split(".")[0]
                matched = False
                for v in variants:
                    if brand_base in v and netloc != brand and not netloc.endswith("." + brand):
                        signals.append({
                            "layer": "rules",
                            "category": "phishing",
                            "signal": f"Look-alike brand impersonation in domain: '{netloc}' mimicking '{brand}'",
                            "score": 88.0
                        })
                        matched = True
                        break
                if matched:
                    break

        return signals

    def evaluate_rules(self, text: str) -> Dict[str, Any]:
        """
        Evaluates rules for phishing, scams, sextortion, threats, insults, and links.
        
        AGGREGATION RULE:
        1. Every signal emitted MUST have a designated 'category' and a 'score'.
        2. category_scores[cat] is updated ONLY by signals filed under that exact category.
        3. No cross-category leakage: a signal labeled 'scam' will NEVER modify 'phishing'.
        """
        text_lower = text.lower()
        text_deobf = deobfuscate_text(text_lower)
        signals: List[Dict[str, Any]] = []

        category_scores = {
            "threat": 0.0,
            "sextortion": 0.0,
            "phishing": 0.0,
            "scam": 0.0,
            "harassment": 0.0,
            "abusive_language": 0.0
        }

        # 1. Link checks (strictly filed under their respective signal categories)
        link_signals = self._analyze_links(text)
        for s in link_signals:
            signals.append(s)
            cat = s["category"]
            category_scores[cat] = max(category_scores[cat], s["score"])

        has_link = len(link_signals) > 0
        has_phish_link = any(s["category"] == "phishing" for s in link_signals)

        # 2. Phishing & Urgency / OTP / KYC
        urgency_hit = any(re.search(pat, text_deobf) for pat in SE_URGENCY_PATTERNS)
        otp_request_hit = any(re.search(pat, text_deobf) for pat in SE_OTP_KYC_REQUEST_PATTERNS)
        genuine_otp_hit = any(re.search(pat, text_lower) for pat in GENUINE_OTP_INDICATORS)
        educational_hit = any(re.search(pat, text_lower) for pat in EDUCATIONAL_SCAM_PATTERNS)

        if educational_hit and not has_link:
            # Educational text discussing scams or warnings is safe/informational
            category_scores["phishing"] = min(category_scores["phishing"], 20.0)
            category_scores["scam"] = min(category_scores["scam"], 20.0)
        elif genuine_otp_hit and not has_link and not urgency_hit:
            # Legitimate automated OTP dispatch (telling user NOT to share)
            pass
        elif otp_request_hit and (urgency_hit or has_phish_link):
            score = 92.0
            category_scores["phishing"] = max(category_scores["phishing"], score)
            signals.append({
                "layer": "rules",
                "category": "phishing",
                "signal": "High-urgency credential, OTP, or KYC verification trap detected",
                "score": score
            })
        elif otp_request_hit:
            score = 80.0
            category_scores["phishing"] = max(category_scores["phishing"], score)
            signals.append({
                "layer": "rules",
                "category": "phishing",
                "signal": "Unsolicited request demanding sensitive OTP or KYC identity credentials",
                "score": score
            })
        elif urgency_hit and has_phish_link:
            score = 74.0
            category_scores["phishing"] = max(category_scores["phishing"], score)
            signals.append({
                "layer": "rules",
                "category": "phishing",
                "signal": "Urgent account suspension warning paired with link",
                "score": score
            })

        # 3. Scams (Lottery, Gift Card, Crypto, Courier/Digital Arrest)
        lottery_hit = any(re.search(pat, text_deobf) for pat in SCAM_LOTTERY_PRIZE_PATTERNS)
        payment_scam_hit = any(re.search(pat, text_deobf) for pat in SCAM_PAYMENT_PATTERNS)
        digital_arrest_hit = any(re.search(pat, text_deobf) for pat in SCAM_COURIER_DIGITAL_ARREST_PATTERNS)

        if not educational_hit:
            if lottery_hit and payment_scam_hit:
                score = 95.0
                category_scores["scam"] = max(category_scores["scam"], score)
                signals.append({
                    "layer": "rules",
                    "category": "scam",
                    "signal": "Lottery/prize award requiring upfront fee via gift card or cryptocurrency",
                    "score": score
                })
            elif lottery_hit:
                score = 82.0
                category_scores["scam"] = max(category_scores["scam"], score)
                signals.append({
                    "layer": "rules",
                    "category": "scam",
                    "signal": "Unsolicited prize or lottery winning notification",
                    "score": score
                })
            elif digital_arrest_hit:
                score = 94.0
                category_scores["scam"] = max(category_scores["scam"], score)
                signals.append({
                    "layer": "rules",
                    "category": "scam",
                    "signal": "Courier/Customs or 'Digital Arrest' extortion scheme impersonating law enforcement",
                    "score": score
                })

        # Phone-call disconnection / penalty scare lures
        phone_lure_hit = any(re.search(pat, text_deobf) for pat in PHONE_CALL_EXTORTION_LURES)
        if phone_lure_hit and not educational_hit:
            score = 85.0
            category_scores["phishing"] = max(category_scores["phishing"], score)
            signals.append({
                "layer": "rules",
                "category": "phishing",
                "signal": "Urgent service disconnection or penalty scare tactic directing user to unverified phone number",
                "score": score
            })

        # Task-based part-time job or work-from-home scams
        job_scam_hit = any(re.search(pat, text_deobf) for pat in TASK_JOB_SCAM_PATTERNS)
        if job_scam_hit and not educational_hit:
            score = 85.0
            category_scores["scam"] = max(category_scores["scam"], score)
            signals.append({
                "layer": "rules",
                "category": "scam",
                "signal": "Task-based part-time job or work-from-home scam directing to messaging app",
                "score": score
            })

        # Crypto extortion / ransomware payment demands
        crypto_extortion_hit = any(re.search(pat, text_deobf) for pat in CRYPTO_EXTORTION_PATTERNS)
        crypto_wallet_match = CRYPTO_WALLET_REGEX.search(text)
        if crypto_extortion_hit and not educational_hit:
            score = 92.0
            category_scores["threat"] = max(category_scores["threat"], score)
            signals.append({
                "layer": "rules",
                "category": "threat",
                "signal": "Cryptocurrency extortion or ransomware payment demand detected",
                "score": score
            })
        elif crypto_wallet_match and any(w in text_deobf for w in ["transfer", "send", "pay", "deposit", "wallet", "usdt", "btc", "bitcoin", "crypto"]) and not educational_hit:
            score = 80.0
            category_scores["scam"] = max(category_scores["scam"], score)
            signals.append({
                "layer": "rules",
                "category": "scam",
                "signal": f"Cryptocurrency wallet payment request detected ({crypto_wallet_match.group(0)[:10]}...)",
                "score": score
            })

        # 4. Sextortion / Photo Blackmail
        sextortion_hit = any(re.search(pat, text_deobf) for pat in SEXTORTION_PATTERNS)
        if sextortion_hit:
            score = 96.0
            category_scores["sextortion"] = max(category_scores["sextortion"], score)
            signals.append({
                "layer": "rules",
                "category": "sextortion",
                "signal": "Sextortion blackmail detected: threat to leak private photos/webcam video",
                "score": score
            })

        # 5. Direct Violence Threats & Severe Death Wishes
        threat_hit = any(re.search(pat, text_deobf) for pat in THREAT_PATTERNS)
        hinglish_threat_hit = any(re.search(pat, text_deobf) for pat in HINGLISH_THREAT_PATTERNS)
        death_wish_hit = any(re.search(pat, text_deobf) for pat in SEVERE_DEATH_WISH_PATTERNS)
        is_gaming_banter = any(re.search(pat, text_lower) for pat in BENIGN_VIOLENT_IDIOM_PATTERNS)

        if threat_hit or hinglish_threat_hit:
            score = 98.0
            category_scores["threat"] = max(category_scores["threat"], score)
            signals.append({
                "layer": "rules",
                "category": "threat",
                "signal": "Explicit physical harm or death threat detected",
                "score": score
            })

        if death_wish_hit:
            score = 82.0
            category_scores["threat"] = max(category_scores["threat"], score)
            category_scores["harassment"] = max(category_scores["harassment"], score)
            signals.append({
                "layer": "rules",
                "category": "threat",
                "signal": "Severe death wish or suicide incitement detected ('kys', 'go die')",
                "score": score
            })

        # 6. Hinglish Scams & Fraud
        hinglish_scam_hit = any(re.search(pat, text_deobf) for pat in HINGLISH_SCAM_PATTERNS)
        if hinglish_scam_hit:
            score = 75.0
            category_scores["scam"] = max(category_scores["scam"], score)
            signals.append({
                "layer": "rules",
                "category": "scam",
                "signal": "Fraudulent banking, KYC, or extortion lure in Roman-script Hindi (Hinglish)",
                "score": score
            })

        # ── SAFETY INVARIANT ──
        # Laughter, banter, and self-directed remarks can ONLY attenuate mild insults.
        # They must NEVER reduce threat, sextortion, blackmail, scam, phishing, or 'kys/you should die' scores.
        has_severe_danger = (
            threat_hit or hinglish_threat_hit or death_wish_hit or sextortion_hit or
            hinglish_scam_hit or otp_request_hit or lottery_hit or digital_arrest_hit or has_phish_link
        )

        # Check benign non-harassment contexts (self-directed, talent idiom, friendly banter)
        if has_severe_danger:
            is_self_directed = False
            is_talent_idiom = False
            is_friendly_banter = False
            is_gaming_banter = False
            is_benign_insult_context = False
        else:
            is_self_directed = any(re.search(pat, text_deobf) for pat in SELF_DIRECTED_PATTERNS)
            is_talent_idiom = any(re.search(pat, text_deobf) for pat in TALENT_IDIOM_PATTERNS)
            is_friendly_banter = any(re.search(pat, text_deobf) for pat in FRIENDLY_BANTER_PATTERNS) or is_gaming_banter
            is_benign_insult_context = is_self_directed or is_talent_idiom or is_friendly_banter

        # 7. Abusive language / Harassment keywords (English & Hinglish)
        insult_hit = any(re.search(pat, text_deobf) for pat in HARASSMENT_INSULT_PATTERNS)
        hinglish_abuse_hit = any(re.search(pat, text_deobf) for pat in HINGLISH_ABUSE_PATTERNS)

        if hinglish_abuse_hit and not is_benign_insult_context:
            score = 75.0
            category_scores["harassment"] = max(category_scores["harassment"], score)
            category_scores["abusive_language"] = max(category_scores["abusive_language"], score)
            signals.append({
                "layer": "rules",
                "category": "abusive_language",
                "signal": "Vulgar Hindi/Hinglish slur or abusive profanity detected",
                "score": score
            })

        if insult_hit and not is_benign_insult_context:
            score = 65.0
            category_scores["harassment"] = max(category_scores["harassment"], score)
            category_scores["abusive_language"] = max(category_scores["abusive_language"], score)
            signals.append({
                "layer": "rules",
                "category": "abusive_language",
                "signal": "Hostile, degrading, or abusive personal insult detected",
                "score": score
            })

        return {
            "category_scores": category_scores,
            "signals": signals
        }

    # ── Explanation & Advice Generators ────────────────────────────────────────

    def _generate_explanation(self, category_scores: Dict[str, float], signals: List[Dict[str, Any]]) -> str:
        """Generates clear, human-readable explanation of findings."""
        sorted_cats = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        top_cat, top_score = sorted_cats[0] if sorted_cats else ("none", 0.0)

        if top_score < 25.0 and not signals:
            return "No malicious indicators detected. The analyzed content appears safe and harmless."

        reasons = [s["signal"] for s in signals]
        unique_reasons = list(dict.fromkeys(reasons))
        top_reasons = unique_reasons[:3]

        if top_cat == "threat" and top_score >= 50.0:
            prefix = "Critical danger: Explicit threats of physical violence were detected."
        elif top_cat == "sextortion" and top_score >= 50.0:
            prefix = "Critical alert: Blackmail or sextortion attempt detected threatening private image leakage."
        elif top_cat == "scam" and top_score >= 50.0:
            prefix = "Fraudulent scam: Fraudulent prize, lottery, courier, or cryptocurrency/gift-card payment pattern detected."
        elif top_cat == "phishing" and top_score >= 50.0:
            prefix = "High risk phishing: Deceptive urgency or fake verification detected trying to steal credentials or financial data."
        elif top_cat == "harassment" and top_score >= 50.0:
            prefix = "Harassment detected: Content contains targeted attacks, hate speech, or severe cyberbullying."
        elif top_cat == "abusive_language" and top_score >= 50.0:
            prefix = "Offensive content: Profane or abusive language was identified."
        else:
            prefix = "Potentially suspicious content detected."

        detail_text = " ".join(f"• {r}" for r in top_reasons)
        return f"{prefix} {detail_text}".strip()

    def _generate_advice(self, category_scores: Dict[str, float]) -> List[str]:
        """Provides actionable safety advice tailored to the incident, including national helplines."""
        advice = []
        sorted_cats = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        top_cat, top_score = sorted_cats[0] if sorted_cats else ("none", 0.0)

        if top_cat == "threat" and top_score >= 25.0:
            advice.append("IMMEDIATE ACTION: Dial Emergency Helpline 112 if you are in immediate physical danger.")
            advice.append("Preserve all unedited screenshots, headers, timestamps, and message links as legal evidence.")
            advice.append("Do not engage, negotiate, or retaliate against the sender.")
            advice.append("File a complaint immediately with your local cyber police station or at https://cybercrime.gov.in.")

        elif top_cat == "sextortion" and top_score >= 25.0:
            advice.append("DO NOT PAY OR SEND MONEY: Paying extortion demands will not stop the attacker and leads to repeated demands.")
            advice.append("Dial National Cyber Crime Helpline 1930 immediately to report the extortion incident.")
            advice.append("Report the incident and request image removal assistance at https://cybercrime.gov.in and StopNCII.org.")
            advice.append("Immediately block the sender on all communication channels and restrict your social media privacy settings.")
            advice.append("Take full screenshots showing the sender's account handle/ID, message text, and timestamp before blocking.")

        elif top_cat == "scam" and top_score >= 25.0:
            advice.append("Legitimate lotteries or official agencies never ask for payment via gift cards or crypto.")
            advice.append("If contacted by callers claiming to be police or customs ('digital arrest'), hang up immediately. Law enforcement does not conduct arrests over video calls.")
            advice.append("Report financial and cyber frauds at https://cybercrime.gov.in or call 1930.")

        elif top_cat == "phishing" and top_score >= 25.0:
            advice.append("DO NOT click any link, scan QR codes, or open attachments received in this message.")
            advice.append("NEVER share OTPs, PINs, passwords, Aadhaar, PAN, or bank credentials over message or phone.")
            advice.append("Report financial fraud attempts immediately to National Cyber Crime Helpline 1930.")
            advice.append("Verify directly by visiting the official banking website or calling the toll-free number printed on the back of your card.")

        elif top_cat == "harassment" and top_score >= 25.0:
            advice.append("Block the abusive profile and report the message to the platform's safety team.")
            advice.append("Document all harassment by capturing full screen evidence with timestamps.")
            advice.append("For persistent harassment or cyberbullying, lodge a formal report at https://cybercrime.gov.in.")

        elif top_cat == "abusive_language" and top_score >= 25.0:
            advice.append("Block the sender and use platform filtering tools to hide abusive commentary.")
            advice.append("If abuse becomes targeted or sustained, preserve copies for reporting.")

        else:
            advice.append("The message appears safe, but always verify unfamiliar senders before sharing personal information.")

        return advice

    def _detect_language(self, text: str) -> Tuple[bool, str, str]:
        """
        Detects whether the input text is in a supported language/script.
        Supported: English and Roman-script Hinglish (uses Latin characters).
        Unsupported: Non-Latin scripts (Devanagari, Tamil, Telugu, Bengali, Arabic, Cyrillic, etc.)
                     and unsupported Latin-script languages (Spanish, French, German, Italian, Portuguese).
        Returns (is_supported: bool, detected_lang: str, note: str).
        """
        if not text or not text.strip():
            return True, "English", ""

        # Strip URLs and link tokens before script detection so web domains don't dilute non-Latin script density
        text_no_url = re.sub(r'https?://\S+|www\.\S+|\b[a-zA-Z0-9.-]+\.(?:com|org|net|xyz|top|site|online|io|in|co|gov|edu)\b', '', text).strip()
        target_script_text = text_no_url if text_no_url else text

        alpha_chars = [c for c in target_script_text if c.isalpha()]
        non_latin = [c for c in target_script_text if ord(c) > 0x024F]

        if non_latin and len(non_latin) >= 4:
            ratio = len(non_latin) / len(alpha_chars) if alpha_chars else 1.0
            if ratio >= 0.25 or len(non_latin) >= 15:
                if any(0x0900 <= ord(c) <= 0x097F for c in non_latin):
                    return False, "Hindi (Devanagari)", "Input text contains Devanagari script. ShieldAI models are calibrated for English and Roman-script Hinglish only; analysis results may be unreliable and cannot be verified as safe."
                elif any(0x0B80 <= ord(c) <= 0x0BFF for c in non_latin):
                    return False, "Tamil", "Input text contains Tamil script. ShieldAI models are calibrated for English and Roman-script Hinglish only; analysis results may be unreliable and cannot be verified as safe."
                elif any(0x0C00 <= ord(c) <= 0x0C7F for c in non_latin):
                    return False, "Telugu", "Input text contains Telugu script. ShieldAI models are calibrated for English and Roman-script Hinglish only; analysis results may be unreliable and cannot be verified as safe."
                elif any(0x0980 <= ord(c) <= 0x09FF for c in non_latin):
                    return False, "Bengali", "Input text contains Bengali script. ShieldAI models are calibrated for English and Roman-script Hinglish only; analysis results may be unreliable and cannot be verified as safe."
                elif any(0x0600 <= ord(c) <= 0x06FF for c in non_latin):
                    return False, "Arabic", "Input text contains Arabic script. ShieldAI models are calibrated for English and Roman-script Hinglish only; analysis results may be unreliable and cannot be verified as safe."
                else:
                    return False, "Non-Latin Script", "Input text contains non-Latin script. ShieldAI models are calibrated for English and Roman-script Hinglish only; analysis results may be unreliable and cannot be verified as safe."

        # Hinglish Protection Invariant:
        # Check distinctive Hinglish vocabulary and pattern rules before external language models
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        distinct_hinglish = {
            "bhai", "yaar", "khelne", "khelo", "khel", "karo", "kare", "karna", "karega", "karegi",
            "bohot", "bahut", "kutta", "kutti", "kutte", "saale", "saala", "chutiye", "chutiya",
            "kamina", "kameene", "bhosadike", "bhosdike", "harami", "dunga", "denge", "dega", "bolta", "bolte",
            "bolti", "milte", "milenge", "shaam", "subah", "paise", "rupaye", "bhejo", "bhejna",
            "samajh", "accha", "theek", "nahin", "nhi", "kaise", "kyun", "kaisa", "kaisi",
            "mera", "meri", "mere", "tera", "teri", "tere", "apna", "apni", "apne",
            "humara", "tumhara", "andar", "baahar", "aao", "jaao", "suno", "dekho", "maar", "maarenge"
        }
        if any(w in distinct_hinglish for w in words):
            return True, "English / Hinglish", ""
        if any(re.search(pat, text.lower()) for pat in (HINGLISH_ABUSE_PATTERNS + HINGLISH_THREAT_PATTERNS + HINGLISH_SCAM_PATTERNS)):
            return True, "English / Hinglish", ""

        # Comprehensive English vocabulary covering conversational and security tokens
        deobf_words = re.findall(r'\b[a-zA-Z]+\b', deobfuscate_text(text.lower()))
        common_en = {
            "the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with",
            "he", "as", "you", "do", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her",
            "she", "or", "an", "will", "my", "one", "all", "would", "there", "their", "what", "so", "up",
            "out", "if", "about", "who", "get", "which", "go", "me", "when", "make", "can", "like", "time",
            "no", "just", "him", "know", "take", "people", "into", "year", "your", "good", "some", "could",
            "them", "see", "other", "than", "then", "now", "look", "only", "come", "its", "over", "think",
            "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way", "even",
            "new", "want", "because", "any", "these", "give", "day", "most", "us", "die", "alone", "ditch",
            "loser", "kill", "shut", "idiot", "stupid", "freak", "clown", "recipe", "umbrella", "kidding",
            "send", "leak", "photos", "nudes", "lol", "haha", "rofl", "again", "botched", "dinner", "got",
            "brother", "chess", "keys", "beat", "round", "match", "team", "sure", "ok", "okay", "thanks",
            "thank", "hello", "hi", "hey", "bye", "yes", "yeah", "yep", "fine", "great", "cool", "morning",
            "night", "tomorrow", "tonight", "later", "please", "help", "here", "there", "where", "why",
            "what", "who", "how", "when", "call", "text", "meet", "lunch", "coffee", "tea", "food", "movie",
            "check", "test", "ready", "done", "am", "is", "are", "was", "were", "been", "has", "had", "did",
            "does", "doing", "having", "going", "went", "came", "seen", "let", "tell", "said", "talk", "chat",
            "speak", "wait", "soon", "late", "today", "yesterday", "man", "bro", "dude", "guy", "guys",
            "friend", "friends", "job", "home", "house", "car", "phone", "email", "link", "page", "code",
            "slides", "presentation", "project", "forgot", "keys", "wallet", "money", "door", "room"
        }

        # Short input check: single/two common English tokens (e.g. "ok", "thanks!", "hey", "hello there")
        if len(words) <= 2:
            if words and all(w in common_en for w in words):
                return True, "English", ""
            elif not words:
                return True, "English", ""

        # English token density check (requiring words of length >= 2 to avoid 'a' or 'i' masking foreign text)
        en_sub_words = [w for w in deobf_words if len(w) >= 2 and w in common_en]
        en_sub_count = len(en_sub_words)
        if deobf_words:
            en_ratio = en_sub_count / len(deobf_words)
            if en_ratio >= 0.40 or (len(deobf_words) <= 4 and en_sub_count >= 2):
                return True, "English", ""

        # Statistical Language Identification via maintained langdetect library
        detected_unsupported_languages = {
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese"
        }

        try:
            from langdetect import detect_langs, DetectorFactory
            DetectorFactory.seed = 42

            # Strip URLs, punctuation, digits to focus on textual language features
            text_clean = re.sub(r'https?://\S+', '', text)
            text_clean = re.sub(r'[^\w\s]', ' ', text_clean)
            text_clean = re.sub(r'\d+', ' ', text_clean).strip()

            if len(text_clean.split()) >= 2:
                candidates = detect_langs(text_clean)
                if candidates:
                    top = candidates[0]
                    if top.lang == "en" and top.prob >= 0.85:
                        return True, "English", ""
                    elif top.prob >= 0.60:
                        lang_name = detected_unsupported_languages.get(top.lang, "Unsupported Language")
                        return False, lang_name, f"Input text appears to be in an unsupported language ({lang_name}). ShieldAI models are calibrated for English and Roman-script Hinglish only; analysis results may be unreliable and cannot be verified as safe."
        except Exception as e:
            logger.debug(f"langdetect evaluation note: {e}")

        # If text has no substantial common English words or Hinglish markers, treat as unverified language
        if en_sub_count == 0 and len(words) >= 2:
            return False, "Unverified Language", "Language unverified. Text contains unknown or non-English vocabulary that cannot be verified as safe."

        return True, "English / Hinglish", ""

    # ── Core Analysis Pipeline ─────────────────────────────────────────────────

    def analyze(self, text: str, precomputed_model_res: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main analysis method for single text.
        Returns full schema: score (0-100), level, category_scores, signals,
        which_layer, explanation, and advice.
        """
        clean_text = (text or "").strip()
        # Empty or single-character trivial strings
        if not clean_text or len(clean_text) <= 2:
            return {
                "score": 0.0,
                "level": "low",
                "category_scores": {
                    "harassment": 0.0,
                    "threat": 0.0,
                    "abusive_language": 0.0,
                    "phishing": 0.0,
                    "scam": 0.0,
                    "sextortion": 0.0
                },
                "signals": [],
                "which_layer": "none",
                "explanation": "No malicious indicators detected. The analyzed content appears safe and harmless." if clean_text else "No text provided.",
                "advice": ["The message appears safe, but always verify unfamiliar senders before sharing personal information."] if clean_text else ["Enter text to analyze."],
                "language_supported": True,
                "language_detected": "English",
                "language_note": ""
            }

        # Check in-memory cache
        if clean_text in self.cache:
            self.cache.move_to_end(clean_text)
            return self.cache[clean_text]

        # Check language support (English & Roman Hinglish supported; non-Latin scripts & Spanish unsupported)
        is_supported, detected_lang, lang_note = self._detect_language(clean_text)
        if not is_supported:
            # Language-independent security checks on unsupported text (URLs, shorteners, look-alike domains, phone lures, crypto wallets)
            link_signals = self._analyze_links(clean_text)
            unsupp_deobf = deobfuscate_text(clean_text.lower())
            extra_signals = []
            unsupp_cats = {
                "harassment": 0.0, "threat": 0.0, "abusive_language": 0.0,
                "phishing": 0.0, "scam": 0.0, "sextortion": 0.0
            }
            for sig in link_signals:
                cat = sig["category"]
                unsupp_cats[cat] = max(unsupp_cats[cat], sig["score"])
                extra_signals.append(sig)

            # Check crypto extortion / wallet in unsupported text
            if any(re.search(pat, unsupp_deobf) for pat in CRYPTO_EXTORTION_PATTERNS):
                unsupp_cats["threat"] = max(unsupp_cats["threat"], 92.0)
                extra_signals.append({
                    "layer": "rules",
                    "category": "threat",
                    "signal": "Cryptocurrency extortion or ransomware payment demand detected",
                    "score": 92.0
                })
            elif CRYPTO_WALLET_REGEX.search(clean_text) and any(w in unsupp_deobf for w in ["transfer", "send", "pay", "deposit", "wallet", "usdt", "btc", "bitcoin", "crypto"]):
                unsupp_cats["scam"] = max(unsupp_cats["scam"], 80.0)
                extra_signals.append({
                    "layer": "rules",
                    "category": "scam",
                    "signal": "Cryptocurrency wallet payment request detected",
                    "score": 80.0
                })

            # Check phone lures in unsupported text
            if any(re.search(pat, unsupp_deobf) for pat in PHONE_CALL_EXTORTION_LURES):
                unsupp_cats["phishing"] = max(unsupp_cats["phishing"], 85.0)
                extra_signals.append({
                    "layer": "rules",
                    "category": "phishing",
                    "signal": "Urgent service disconnection or penalty scare tactic directing user to unverified phone number",
                    "score": 85.0
                })

            max_sec_score = max(unsupp_cats.values())
            if max_sec_score >= 50.0:
                # Real security threat detected despite unsupported language!
                sec_level = "critical" if max_sec_score >= 75.0 else "high"
                return {
                    "score": round(max_sec_score, 1),
                    "level": sec_level,
                    "category_scores": unsupp_cats,
                    "signals": extra_signals,
                    "which_layer": "rules",
                    "explanation": f"Actionable threat indicators detected in text ({detected_lang}). Linguistic analysis is unsupported and may be unreliable.",
                    "advice": ["Actionable cyber threat detected. Do not click links, call numbers, or transfer funds."],
                    "model_active": self.is_loaded,
                    "language_supported": False,
                    "language_detected": detected_lang,
                    "language_note": lang_note
                }
            else:
                return {
                    "score": 0.0,
                    "level": "unsupported",
                    "category_scores": unsupp_cats,
                    "signals": [{
                        "signal": f"Unsupported language/script detected: {detected_lang}. Results may be unreliable.",
                        "category": "language_unsupported",
                        "severity": "medium",
                        "pattern": detected_lang
                    }],
                    "which_layer": "language_filter",
                    "explanation": lang_note,
                    "advice": [
                        "ShieldAI is calibrated for English and Roman-script Hinglish.",
                        "Analysis for this script/language cannot be verified as safe."
                    ],
                    "model_active": self.is_loaded,
                    "language_supported": False,
                    "language_detected": detected_lang,
                    "language_note": lang_note
                }

        # Normalize text before model and rules (leetspeak, zero-width chars, mixed spacing, symbols)
        norm_text = normalize_text(clean_text)
        text_lower = norm_text.lower()
        text_deobf = deobfuscate_text(text_lower)

        # ── SAFETY INVARIANT: Severe threats, sextortion, scams & death wishes CAN NEVER be attenuated ──
        has_severe_threat = (
            any(re.search(pat, text_deobf) for pat in THREAT_PATTERNS) or
            any(re.search(pat, text_deobf) for pat in SEVERE_DEATH_WISH_PATTERNS) or
            any(re.search(pat, text_deobf) for pat in HINGLISH_THREAT_PATTERNS) or
            any(re.search(pat, text_deobf) for pat in SEXTORTION_PATTERNS) or
            any(re.search(pat, text_deobf) for pat in HINGLISH_SCAM_PATTERNS) or
            any(re.search(pat, text_deobf) for pat in SCAM_LOTTERY_PRIZE_PATTERNS) or
            any(re.search(pat, text_deobf) for pat in SCAM_PAYMENT_PATTERNS) or
            any(re.search(pat, text_deobf) for pat in SCAM_COURIER_DIGITAL_ARREST_PATTERNS) or
            any(re.search(pat, text_deobf) for pat in SE_OTP_KYC_REQUEST_PATTERNS)
        )

        if has_severe_threat:
            is_gaming_banter = False
            is_self_directed = False
            is_talent_idiom = False
            is_friendly_banter = False
            is_benign_insult_context = False
        else:
            is_gaming_banter = any(re.search(pat, text_lower) for pat in BENIGN_VIOLENT_IDIOM_PATTERNS)
            is_self_directed = any(re.search(pat, text_lower) for pat in SELF_DIRECTED_PATTERNS)
            is_talent_idiom = any(re.search(pat, text_lower) for pat in TALENT_IDIOM_PATTERNS)
            is_friendly_banter = any(re.search(pat, text_lower) for pat in FRIENDLY_BANTER_PATTERNS) or is_gaming_banter
            is_benign_insult_context = is_self_directed or is_talent_idiom or is_friendly_banter

        # 1. Neural Model Inference (run on normalized text)
        if precomputed_model_res is not None:
            model_res = precomputed_model_res
        else:
            model_res = self._predict_model_batch([norm_text])[0]
        model_scores = model_res.get("scores", {})
        model_probs = model_res.get("probs", {})
        model_active = model_res.get("active", False)

        model_signals: List[Dict[str, Any]] = []
        model_threat = 0.0
        model_harassment = 0.0
        model_abusive = 0.0

        if model_active:
            # Threat
            threat_p = model_probs.get("Threat", 0.0)
            threat_thresh = self.thresholds.get("Threat", 0.5332)
            threat_rel = model_scores.get("Threat", 0.0)
            
            # Neutralize violent words when clearly used in friendly gaming banter
            if is_gaming_banter:
                threat_rel = min(threat_rel * 0.15, 20.0)
                threat_p = min(threat_p, 0.20)

            model_threat = threat_rel
            if threat_p >= threat_thresh:
                model_signals.append({
                    "layer": "model",
                    "category": "threat",
                    "signal": f"Model flagged high-confidence threat ({threat_p*100:.1f}% vs threshold {threat_thresh*100:.1f}%)",
                    "score": threat_rel
                })

            # Harassment (Hate Speech + Cyberbullying)
            hate_p = model_probs.get("Hate Speech", 0.0)
            hate_thresh = self.thresholds.get("Hate Speech", 0.8076)
            cb_p = model_probs.get("Cyberbullying / Harassment", 0.0)
            cb_thresh = self.thresholds.get("Cyberbullying / Harassment", 0.8905)

            hate_rel = model_scores.get("Hate Speech", 0.0)
            cb_rel = model_scores.get("Cyberbullying / Harassment", 0.0)

            # Attenuate harassment scores when benign banter, self-directed, or talent compliment context
            if is_benign_insult_context:
                hate_rel = min(hate_rel * 0.15, 20.0)
                hate_p = min(hate_p, 0.20)
                cb_rel = min(cb_rel * 0.15, 20.0)
                cb_p = min(cb_p, 0.20)

            model_harassment = max(hate_rel, cb_rel)

            if hate_p >= hate_thresh and not is_benign_insult_context:
                model_signals.append({
                    "layer": "model",
                    "category": "harassment",
                    "signal": f"Model flagged hate speech ({hate_p*100:.1f}% vs threshold {hate_thresh*100:.1f}%)",
                    "score": hate_rel
                })
            if cb_p >= cb_thresh and not is_benign_insult_context:
                model_signals.append({
                    "layer": "model",
                    "category": "harassment",
                    "signal": f"Model flagged cyberbullying/harassment ({cb_p*100:.1f}% vs threshold {cb_thresh*100:.1f}%)",
                    "score": cb_rel
                })

            # Abusive language (Toxicity + Profanity)
            tox_p = model_probs.get("Toxicity / Offensive Language", 0.0)
            tox_thresh = self.thresholds.get("Toxicity / Offensive Language", 0.4210)
            prof_p = model_probs.get("Profanity", 0.0)
            prof_thresh = self.thresholds.get("Profanity", 0.9966)

            tox_rel = model_scores.get("Toxicity / Offensive Language", 0.0)
            prof_rel = model_scores.get("Profanity", 0.0)

            if is_benign_insult_context:
                tox_rel = min(tox_rel * 0.25, 25.0)
                tox_p = min(tox_p, 0.20)
                prof_rel = min(prof_rel * 0.25, 25.0)
                prof_p = min(prof_p, 0.20)

            # Check if text contains explicit profane words from lexicon
            has_profane_word = any(re.search(pat, text_lower) for pat in PROFANITY_WORD_PATTERNS)
            if not has_profane_word:
                # Down-weight Profanity label heavily when no profane word is present in the text
                prof_rel = min(prof_rel * 0.2, 20.0)

            # Toxicity & Profanity lower weight
            model_abusive = max(tox_rel, prof_rel) * 0.7

            if tox_p >= tox_thresh and not is_benign_insult_context:
                model_signals.append({
                    "layer": "model",
                    "category": "abusive_language",
                    "signal": f"Model flagged toxic language ({tox_p*100:.1f}% vs threshold {tox_thresh*100:.1f}%)",
                    "score": tox_rel
                })

            # Avoid claiming profanity unless a word list also confirms it
            if prof_p >= prof_thresh and has_profane_word:
                model_signals.append({
                    "layer": "model",
                    "category": "abusive_language",
                    "signal": f"Model flagged profanity ({prof_p*100:.1f}% vs threshold {prof_thresh*100:.1f}%)",
                    "score": prof_rel
                })

        # 2. Rules Inference (evaluated on original clean text with internal deobfuscation)
        rules_res = self.evaluate_rules(clean_text)
        rules_cats = rules_res["category_scores"]
        rules_signals = rules_res["signals"]

        # 3. Hybrid Blending & Scoring
        # Threat: use the HIGHER of model and rules as specified
        final_threat = max(model_threat, rules_cats["threat"])

        # Sextortion: model does not cover sextortion; rules provide base, boosted if model flags threat/harassment
        final_sextortion = rules_cats["sextortion"]
        if final_sextortion > 0 and (model_threat > 50 or model_harassment > 50):
            final_sextortion = min(100.0, final_sextortion + 3.0)

        # Phishing & Scams: model does not cover; driven strictly by rules + links
        final_phishing = rules_cats["phishing"]
        final_scam = rules_cats["scam"]

        # Harassment: hybrid blend (model and rules assist each other)
        if model_active:
            # Let the neural model decide English abuse categories;
            # rules augment for Hinglish abuse, severe death wishes, and sextortion.
            is_non_model_abuse = (
                any(re.search(pat, text_deobf) for pat in HINGLISH_ABUSE_PATTERNS) or
                any(re.search(pat, text_deobf) for pat in SEVERE_DEATH_WISH_PATTERNS)
            )
            final_harassment = max(
                model_harassment,
                rules_cats["harassment"] if is_non_model_abuse else 0.0,
                0.85 * model_harassment + 0.15 * rules_cats["harassment"]
            )
            final_abusive = max(
                model_abusive,
                rules_cats["abusive_language"] if is_non_model_abuse else 0.0,
                0.80 * model_abusive + 0.20 * rules_cats["abusive_language"]
            )
        else:
            final_harassment = rules_cats["harassment"]
            final_abusive = rules_cats["abusive_language"]

        # Clean sanity check
        clean_p = model_probs.get("Clean", 0.0) if model_active else 0.0
        clean_thresh = self.thresholds.get("Clean", 0.5179)
        all_rules_zero = all(v == 0.0 for v in rules_cats.values())

        if clean_p >= clean_thresh and all_rules_zero and model_threat < 35 and model_harassment < 35:
            final_threat = min(final_threat, 10.0)
            final_harassment = min(final_harassment, 10.0)
            final_abusive = min(final_abusive, 10.0)

        final_category_scores = {
            "threat": round(final_threat, 1),
            "sextortion": round(final_sextortion, 1),
            "phishing": round(final_phishing, 1),
            "scam": round(final_scam, 1),
            "harassment": round(final_harassment, 1),
            "abusive_language": round(final_abusive, 1)
        }

        # Overall risk score calculation:
        primary_risks = [
            final_threat,
            final_sextortion,
            final_phishing,
            final_scam,
            final_harassment,
            final_abusive * 0.8
        ]
        max_score = max(primary_risks)

        # Multi-category reinforcement bonus (max 5%)
        active_high_cats = sum(1 for s in primary_risks if s >= 50.0)
        multi_boost = min(5.0, (active_high_cats - 1) * 2.5) if active_high_cats > 1 else 0.0

        overall_score = round(min(100.0, max_score + multi_boost), 1)

        combined_signals = model_signals + rules_signals

        # ── Severity Caps & Critical Level Eligibility ────────────────────────
        # CRITICAL level is reserved ONLY for:
        # 1. Threats (physical violence, death threats)
        # 2. Sextortion (webcam/intimate photo blackmail)
        # 3. Hate Speech (identity attack, racism, religious hatred)
        # 4. Scams or Phishing with strong verified signals (malicious links, OTP/credential traps)
        # Plain insults, cyberbullying, or abusive language are capped at plain_abuse_cap (default 80.0, High level).
        is_threat = final_threat >= 75.0
        is_sextortion = final_sextortion >= 75.0
        is_hate_speech = (
            (model_active and model_probs.get("Hate Speech", 0.0) >= self.thresholds.get("Hate Speech", 0.6567))
            or any(s["category"] == "harassment" and "hate speech" in s["signal"].lower() for s in combined_signals)
        )
        has_strong_phishing = any(
            s["category"] == "phishing" and s.get("score", 0) >= 80.0
            for s in rules_signals
        )
        has_strong_scam = any(
            s["category"] == "scam" and s.get("score", 0) >= 80.0
            for s in rules_signals
        )
        is_strong_fraud = (final_phishing >= 75.0 and has_strong_phishing) or (final_scam >= 75.0 and has_strong_scam)

        has_severe_death_wish = any(
            s.get("category") == "threat" and "severe death wish" in s.get("signal", "").lower()
            for s in rules_signals
        )
        is_critical_eligible = is_threat or is_sextortion or is_hate_speech or is_strong_fraud or has_severe_death_wish

        abuse_cap = self.severity_caps.get("plain_abuse_cap", 80.0)
        if not is_hate_speech and not has_severe_death_wish:
            final_category_scores["harassment"] = min(final_category_scores["harassment"], abuse_cap)
            final_category_scores["abusive_language"] = min(final_category_scores["abusive_language"], abuse_cap)

        # Single-label marginal toxicity calibration:
        # If the only active category is mild/marginal toxicity (abusive_language score < 65.0)
        # with zero threat, sextortion, scam, phishing, or harassment, it should be medium risk at most, not high.
        is_marginal_single_label_tox = (
            final_category_scores["abusive_language"] >= 50.0 and
            final_category_scores["abusive_language"] < 65.0 and
            final_category_scores["harassment"] < 35.0 and
            final_category_scores["threat"] == 0.0 and
            final_category_scores["sextortion"] == 0.0 and
            final_category_scores["phishing"] == 0.0 and
            final_category_scores["scam"] == 0.0 and
            not is_critical_eligible
        )

        if not is_critical_eligible:
            overall_score = min(overall_score, abuse_cap)
            if is_marginal_single_label_tox:
                level = "medium"
            elif overall_score >= 50.0:
                level = "high"
            elif overall_score >= 25.0:
                level = "medium"
            else:
                level = "low"
        else:
            if overall_score >= 75.0:
                level = "critical"
            elif overall_score >= 50.0:
                level = "high"
            elif overall_score >= 25.0:
                level = "medium"
            else:
                level = "low"

        # Determine which layer produced output
        has_model_signals = len(model_signals) > 0
        has_rules_signals = len(rules_signals) > 0

        if has_model_signals and has_rules_signals:
            which_layer = "hybrid"
        elif has_model_signals:
            which_layer = "model"
        elif has_rules_signals:
            which_layer = "rules"
        else:
            which_layer = "model" if model_active else "rules"

        explanation = self._generate_explanation(final_category_scores, combined_signals)
        advice = self._generate_advice(final_category_scores)

        result = {
            "score": overall_score,
            "level": level,
            "category_scores": final_category_scores,
            "signals": combined_signals,
            "which_layer": which_layer,
            "explanation": explanation,
            "advice": advice,
            "language_supported": True,
            "language_detected": detected_lang,
            "language_note": ""
        }

        # Save to LRU cache
        if len(self.cache) >= self.max_cache_size:
            self.cache.popitem(last=False)
        self.cache[clean_text] = result

        return result

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """Batch analysis for the Chrome extension endpoint."""
        results = []
        uncached_indices = []
        uncached_texts = []

        # Check cache first
        for i, text in enumerate(texts):
            clean_t = (text or "").strip()
            if clean_t in self.cache:
                self.cache.move_to_end(clean_t)
                results.append(self.cache[clean_t])
            else:
                results.append(None)
                uncached_indices.append(i)
                uncached_texts.append(clean_t)

        if uncached_texts:
            model_batch_res = self._predict_model_batch(uncached_texts)

            for idx, raw_t, m_res in zip(uncached_indices, uncached_texts, model_batch_res):
                if not raw_t:
                    empty_res = {
                        "score": 0.0,
                        "level": "low",
                        "category_scores": {k: 0.0 for k in ["harassment", "threat", "abusive_language", "phishing", "scam", "sextortion"]},
                        "signals": [],
                        "which_layer": "none",
                        "explanation": "No text provided.",
                        "advice": ["Enter text to analyze."]
                    }
                    results[idx] = empty_res
                    continue

                item_res = self.analyze(raw_t, precomputed_model_res=m_res)
                results[idx] = item_res

        return results


# Module-level convenience singleton
model_service = ModelService.get_instance()
