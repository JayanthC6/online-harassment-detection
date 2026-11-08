import re

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
    # General single * inside a word -> i (e.g., d*e -> die)
    norm = re.sub(r'(?<=[a-zA-Z])\*(?=[a-zA-Z])', 'i', norm)

    # 4. Leetspeak & symbol substitutions
    # ! or 1 inside word -> i
    norm = re.sub(r'(?<=[a-zA-Z])[!1]+(?=[a-zA-Z]|\b)', lambda m: 'i' * len(m.group(0)), norm)
    norm = re.sub(r'\b[!1]+(?=[a-zA-Z]{2,})', lambda m: 'i' * len(m.group(0)), norm)
    # 3 inside word -> e (e.g. fr33 -> free, h3ll -> hell)
    norm = re.sub(r'(?<=[a-zA-Z])3+', lambda m: 'e' * len(m.group(0)), norm)
    norm = re.sub(r'\b3+(?=[a-zA-Z]{2,})', lambda m: 'e' * len(m.group(0)), norm)
    # 0 inside word -> o
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

test_inputs = [
    'I will k!ll you',
    'He is going to k1ll them',
    'What the f*ck is this',
    'Click for fr33 b!tcoin rewards',
    'You should d i e alone',
    'k i l l yourself now',
    'fuuuuuck you idiot',
    'sooooo sweet and nice',
    'Zero\u200bwidth\u200cspaces',
    'Download this g!ft c@rd now http://win-card.top',
    'Your OTP for transaction of INR 4,500.00 at Amazon with SBI Card ending 4012 is 829104. Never share OTP with anyone.'
]

for t in test_inputs:
    print(f"{t!r:45} -> {normalize_text(t)!r}")
