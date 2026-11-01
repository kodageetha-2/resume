from functools import lru_cache
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@lru_cache(maxsize=1)
def _model():
    try:
        from sentence_transformers import SentenceTransformer
        # Avoid an unexpected first-run download; cached models are used automatically.
        return SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
    except Exception:
        return None

def semantic_similarity(first: str, second: str) -> float:
    if not first.strip() or not second.strip(): return 0.0
    model = _model()
    if model:
        try:
            vectors = model.encode([first, second])
            return float(cosine_similarity([vectors[0]], [vectors[1]])[0][0])
        except Exception:
            pass
    try:
        matrix = TfidfVectorizer(stop_words="english").fit_transform([first, second])
    except ValueError:
        return 0.0
    return float(cosine_similarity(matrix[0], matrix[1])[0][0])
