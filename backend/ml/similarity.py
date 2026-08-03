"""
Duplicate / similar report detection using sentence-transformers.

Embeds each flagged report with all-MiniLM-L6-v2 (~22MB download on first run)
and computes cosine similarity against previous reports.

Threshold: 0.75 — captures paraphrases and rewordings while excluding
merely topic-related text. This is the standard "high semantic similarity"
threshold validated across sentence-transformers benchmarks (STS-B, MRPC).
"""
import os
import numpy as np

_model = None


def _load_model():
    """Lazy-load the sentence transformer model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_text(text: str) -> list:
    """Return the embedding vector for a text string, as a plain Python list."""
    model = _load_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding.tolist()


def cosine_similarity(vec_a, vec_b) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


SIMILARITY_THRESHOLD = 0.75


def find_similar_reports(text: str, existing_reports: list, threshold: float = SIMILARITY_THRESHOLD) -> list:
    """
    Find reports in existing_reports that are semantically similar to `text`.

    Args:
        text: the new report text to compare
        existing_reports: list of dicts, each with at least 'text_preview' and 'embedding' keys
        threshold: cosine similarity threshold (default 0.75)

    Returns:
        list of dicts: [{text_preview, similarity, index}, ...] for reports above threshold,
        sorted by similarity descending.
    """
    new_embedding = embed_text(text)
    matches = []

    for i, report in enumerate(existing_reports):
        embedding = report.get("embedding")
        if embedding is None:
            continue
        sim = cosine_similarity(new_embedding, embedding)
        if sim >= threshold:
            matches.append({
                "text_preview": report.get("text_preview", "")[:80],
                "similarity": round(sim, 3),
                "index": i,
            })

    matches.sort(key=lambda x: x["similarity"], reverse=True)
    return matches, new_embedding
