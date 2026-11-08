import hashlib
import logging
from pathlib import Path
from backend.services.csv_parser import enrich_csv
from backend.database.term_repository import process_csv_to_pg_db
from backend.services.indexing import index_file

logger = logging.getLogger(__name__)


async def retry_file_index(filepath: str):
    try:
        await index_file(filepath)
    except LookupError:
        raise
    except Exception:
        logger.exception(
            "Indexing failed for %s; PostgreSQL data is retained", filepath)
        return {"status": "indexing_pending", "path": filepath, "retryable": True}
    return {"status": "indexed", "path": filepath, "retryable": False}


async def process_csv_to_db(filepath: str, category: str, subject: str):
    subject_id = hashlib.sha1(
        subject.strip().lower().encode("utf-8")).hexdigest()
    category_id = hashlib.sha1(
        category.strip().lower().encode("utf-8")).hexdigest()
    enriched_path = enrich_csv(filepath, category_id, subject_id)
    try:
        await process_csv_to_pg_db(
            filepath, enriched_path, category, category_id, subject, subject_id
        )
    finally:
        Path(enriched_path).unlink(missing_ok=True)

    # Also handles first inserts
    # Considering postgres successful insert we need chroma indexing to be done,
    # if it fails we need to retry it otherwise one database is partially updated
    # and the other is full which isnt acceptable.
    return await retry_file_index(filepath)
