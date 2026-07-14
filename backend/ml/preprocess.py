"""
Text preprocessing utilities for the Online Harassment Detection System.

Used identically at training time and inference time so the model always
sees text in the same shape it was trained on.
"""
import re
import nltk
from nltk.corpus import stopwords

# Download once; no-ops if already present.
for pkg in ("stopwords", "punkt"):
    try:
        nltk.data.find(f"corpora/{pkg}" if pkg == "stopwords" else f"tokenizers/{pkg}")
    except LookupError:
        nltk.download(pkg, quiet=True)

STOPWORDS = set(stopwords.words("english"))

URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"@\w+")
RT_RE = re.compile(r"^rt\s+", re.IGNORECASE)
NON_ALPHA_RE = re.compile(r"[^a-zA-Z\s']")
MULTI_SPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Lowercase, strip URLs/mentions/RT markers/punctuation, collapse whitespace."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = RT_RE.sub("", text)
    text = URL_RE.sub("", text)
    text = MENTION_RE.sub("", text)
    text = NON_ALPHA_RE.sub(" ", text)
    text = MULTI_SPACE_RE.sub(" ", text).strip()
    return text


def remove_stopwords(text: str) -> str:
    return " ".join(w for w in text.split() if w not in STOPWORDS)


def preprocess(text: str, strip_stopwords: bool = True) -> str:
    """Full pipeline: clean -> (optionally) remove stopwords."""
    cleaned = clean_text(text)
    if strip_stopwords:
        cleaned = remove_stopwords(cleaned)
    return cleaned


if __name__ == "__main__":
    sample = "RT @someone: You're pathetic, nobody wants you here!!! https://t.co/abc123"
    print("raw:      ", sample)
    print("processed:", preprocess(sample))
