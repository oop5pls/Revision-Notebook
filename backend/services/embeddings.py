from typing import List

def embed_text(text: str) -> List[float]:
    """
    Turn a single string into a vector using all-MiniLM-L6-v2
    """
    # TODO: Implement SentenceTransformer.encode()
    return []

def embed_batch(texts: List[str]) -> List[List[float]]:
    """
    Turn a list of strings into a list of vectors (Optimized)
    """
    # TODO: Implement SentenceTransformer.encode(texts)
    return [[]]
