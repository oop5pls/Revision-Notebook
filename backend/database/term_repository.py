import time
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.database.connection import engine
import backend.models.db_models as models


async def process_csv_to_pg_db(filepath: str, enriched_path: str, category: str, category_id: str, subject: str, subject_id: str):
    start_total = time.perf_counter()

    start_db = time.perf_counter()
    async with AsyncSession(engine) as session:
        await session.exec(
            insert(models.Subject).values(
                subject_id=subject_id,
                subject=subject.strip().lower(),
            ).on_conflict_do_nothing(index_elements=["subject_id"])
        )
        await session.exec(
            insert(models.Category).values(
                category_id=category_id,
                category_name=category.strip().lower(),
            ).on_conflict_do_nothing(index_elements=["category_id"])
        )
        await session.exec(
            insert(models.Files).values(full_file_name=filepath)
        )

        print("[DEBUG] so far so good")

        # Print first 5 rows of enriched CSV for debugging
        print("[DEBUG] First 5 rows of enriched CSV:")
        with open(enriched_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 6:  # header + 5 data rows
                    break
                print(f"  {line.rstrip()}")

        start_conn = time.perf_counter()
        connection = await session.connection()
        raw_connection = await connection.get_raw_connection()
        print(
            f"[DEBUG] Connection acquisition took: {time.perf_counter() - start_conn:.4f}s")

        start_copy = time.perf_counter()
        print(f"[DEBUG] Starting copy_to_table at {start_copy}")
        await raw_connection.driver_connection.copy_to_table(
            "terms",
            source=enriched_path,
            columns=[
                "term",
                "definition",
                "term_id",
                "subject_id",
                "category_id",
                "file_of_origin"
            ],
            format="csv",
            header=True,
        )
        print(
            f"[DEBUG] copy_to_table took: {time.perf_counter() - start_copy:.4f}s")

        await session.commit()
        print(
            f"[DEBUG] DB transaction total took: {time.perf_counter() - start_db:.4f}s")
        print(
            f"[DEBUG] Successfully committed data to database for: {filepath}")

    print(
        f"[DEBUG] Total process_csv_to_db took: {time.perf_counter() - start_total:.4f}s")


async def process_excel_to_pg_db(file_path: str):
    pass


async def iter_file_term_batches(filepath: str, batch_size: int = 100):
    async with AsyncSession(engine) as session:
        exists = await session.execute(
            text("SELECT 1 FROM files WHERE full_file_name = :path"), {"path": filepath}
        )
        if exists.scalar_one_or_none() is None:
            raise LookupError(filepath)
        result = await session.stream(
            text("SELECT term_id, term, definition, subject_id, category_id, file_of_origin "
                 "FROM terms WHERE file_of_origin = :path"), {"path": filepath}
        )
        try:
            async for rows in result.mappings().partitions(batch_size):
                yield rows
        finally:
            await result.close()
