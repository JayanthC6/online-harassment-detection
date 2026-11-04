"""
Duplicate / similar report detection using sentence-transformers.

Embeds each flagged report with all-MiniLM-L6-v2
and computes cosine similarity against previous reports.

Threshold: 0.75 — captures paraphrases and rewordings while excluding
merely topic-related text.
"""
import os
import logging
import numpy as np

_model = None
_model_failed = False


def _load_model():
    """Lazy-load the sentence transformer model with fast safe fallback."""
    global _model, _model_failed
    if _model_failed:
        return None
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Fast check: try local cache without network freeze
            _model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
        except Exception as e:
            logging.info(f"SentenceTransformer not cached locally, semantic similarity disabled: {e}")
            _model_failed = True
            return None
    return _model


def embed_text(text: str) -> list:
    """Return the embedding vector for a text string, as a plain Python list."""
    model = _load_model()
    if model is None:
        return []
    try:
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    except Exception as e:
        logging.warning(f"Embedding encoding error: {e}")
        return []


def cosine_similarity(vec_a, vec_b) -> float:
    """Compute cosine similarity between two vectors."""
    if not vec_a or not vec_b:
        return 0.0
    a = np.array(vec_a)
    b = np.array(vec_b)
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))


SIMILARITY_THRESHOLD = 0.75


def find_similar_reports(text: str, existing_reports: list, threshold: float = SIMILARITY_THRESHOLD):
    """
    Find reports in existing_reports that are semantically similar to `text`.
    """
    new_embedding = embed_text(text)
    if not new_embedding:
        return [], None
        
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
