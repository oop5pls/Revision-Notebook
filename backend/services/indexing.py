from asyncio import to_thread
from backend.chroma.term_repository import upsert_documents
from backend.database.term_repository import iter_file_term_batches


async def index_file(filepath: str):
    """Rebuild a file's index from committed PostgreSQL rows, safely on retries."""
    async for rows in iter_file_term_batches(filepath):
        ids = [row["term_id"] for row in rows]
        documents = [f"Term: {row['term']}\nDefinition: {row['definition']}" for row in rows]
        metadata = [
            {key: row[key] for key in ("term", "subject_id", "category_id", "file_of_origin")
             if row[key] is not None}
            for row in rows
        ]
        await to_thread(upsert_documents, ids, documents, metadata)
