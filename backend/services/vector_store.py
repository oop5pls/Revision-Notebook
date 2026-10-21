from typing import List

def upsert_vectors(ids: List[str], vectors: List[List[float]], metadata: List[dict]):
    """
    Store or update vectors in ChromaDB
    """
    # TODO: Implement chroma_collection.upsert()
    pass

def query_vectors(query_vector: List[float], top_k: int = 5) -> List[str]:
    """
    Find the top K closest IDs
    """
    # TODO: Implement chroma_collection.query()
    return []

def delete_vector(vector_id: str):
    """
    Remove a vector from the index
    """
    # TODO: Implement chroma_collection.delete()
    pass
