import magic
import hashlib
import csv
import uuid
import tempfile
import os
import time
from sqlmodel import insert, text
from backend.database_services.database_conn import engine
import backend.models.db_models as models
from sqlmodel.ext.asyncio.session import AsyncSession
import threading


def validate_file_type(file_stream, filename: str = "") -> bool:
    if filename.lower().endswith('.csv'):
        sample = file_stream.read(2048)
        file_stream.seek(0)
        try:
            csv.Sniffer().sniff(sample.decode('utf-8', errors='ignore')[:1024])
            return True
        except Exception:
            raise ValueError(
                "File has .csv extension but is not valid CSV format")

    mime = magic.from_buffer(file_stream.read(2048), mime=True)
    file_stream.seek(0)

    allowed_types = ['text/csv', 'application/vnd.ms-excel',
                     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    if mime not in allowed_types:
        raise ValueError(f"Unsupported file type: {mime}")
    return True


async def save_upload_file(upload_file):
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    filename = upload_file.filename.replace(
        "/", "_").replace("\\", "_").replace("..", "_").replace(" ", "_")
    destination = os.path.join(upload_dir, filename)
    with open(destination, "wb") as buffer:
        while True:
            chunk = await upload_file.read(1024*1024)

            if not chunk:
                break
            buffer.write(chunk)

    return destination


def enrich_csv(filepath: str, category_id: str, subject_id: str):
    print(f"[DEBUG] Enriching CSV: {filepath}")
    start = time.perf_counter()
    temp_fd, temp_path = tempfile.mkstemp(suffix=".csv")
    try:
        with open(filepath, mode="r", encoding="utf-8") as infile:
            reader = csv.reader(infile)
            header = next(reader, None)

            with open(temp_path, mode="w", encoding="utf-8", newline="") as outfile:
                writer = csv.writer(outfile)

                if header:
                    # Append new columns to header
                    writer.writerow(
                        header + ["term_id", "subject_id", "category_id", "file_of_origin"])

                    for row in reader:
                        # Append values to each row
                        # deterministic term_id: sha1(term + definition + file_of_origin)
                        term_content = "".join(row[:2]) + filepath
                        term_id = hashlib.sha1(
                            term_content.encode("utf-8")).hexdigest()
                        writer.writerow(
                            row + [term_id, subject_id, category_id, filepath])
                else:
                    # Handle empty file
                    pass
    finally:
        os.close(temp_fd)

    print(f"[DEBUG] CSV Enrichment took: {time.perf_counter() - start:.4f}s")

    return temp_path


async def process_csv_to_db(filepath: str, category: str, subject: str):
    print(f"[DEBUG] Starting database insertion for file: {filepath}")
    start_total = time.perf_counter()
    subject_id = hashlib.sha1(
        (subject.strip().lower()).encode("utf-8")).hexdigest()
    category_id = hashlib.sha1(
        (category.strip().lower()).encode("utf-8")).hexdigest()

    enriched_path = enrich_csv(filepath, category_id, subject_id)

    try:
        start_db = time.perf_counter()
        async with AsyncSession(engine) as session:
            await session.exec(
                insert(models.Subject).values(
                    subject_id=subject_id,
                    subject=subject,
                )
            )
            await session.exec(
                insert(models.Category).values(
                    category_id=category_id,
                    category_name=category,
                )
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
    finally:
        if os.path.exists(enriched_path):
            os.remove(enriched_path)

    print(
        f"[DEBUG] Total process_csv_to_db took: {time.perf_counter() - start_total:.4f}s")


async def process_excel_to_db(file_path: str):
    pass
