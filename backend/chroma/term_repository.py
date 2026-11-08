from backend.chroma.connection import get_collection


def upsert_documents(ids, documents, metadata):
    if ids:
        get_collection().upsert(ids=ids, documents=documents, metadatas=metadata)


def upsert_vectors(ids, vectors, metadata):
    if ids:
        get_collection().upsert(ids=ids, embeddings=vectors, metadatas=metadata)


def query_vectors(query_vector, top_k=5):
    collection = get_collection()
    count = collection.count()
    if count == 0 or top_k <= 0:
        return []
    result = collection.query(query_embeddings=[query_vector], n_results=min(top_k, count))
    return result["ids"][0]


def delete_vector(vector_id):
    get_collection().delete(ids=[vector_id])
