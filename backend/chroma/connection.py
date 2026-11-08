from functools import lru_cache
import os
from pathlib import Path


@lru_cache(maxsize=1)
def get_client():
    import chromadb

    default_path = Path(__file__).resolve().parents[2] / "chroma_data"
    return chromadb.PersistentClient(path=os.getenv("CHROMA_PATH", str(default_path)))


@lru_cache(maxsize=1)
def get_collection():
    return get_client().get_or_create_collection(
        name=os.getenv("CHROMA_COLLECTION", "terms")
    )
