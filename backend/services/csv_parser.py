import csv
import hashlib
import os
from pathlib import Path
import tempfile


def enrich_csv(filepath: str, category_id: str, subject_id: str):
    temp_fd, temp_path = tempfile.mkstemp(suffix=".csv")
    os.close(temp_fd)
    try:
        with open(filepath, encoding="utf-8-sig", newline="") as infile, open(
            temp_path, "w", encoding="utf-8", newline=""
        ) as outfile:
            reader = csv.reader(infile, strict=True)
            header = next(reader, None)
            if not header or len(header) != 2:
                raise ValueError("CSV must have two columns: term and definition")
            writer = csv.writer(outfile)
            writer.writerow(header + ["term_id", "subject_id", "category_id", "file_of_origin"])
            count = 0
            for row in reader:
                if len(row) != 2 or not all(value.strip() for value in row):
                    raise ValueError(f"Invalid term or definition at CSV line {reader.line_num}")
                term_id = hashlib.sha1(("".join(row) + filepath).encode("utf-8")).hexdigest()
                writer.writerow(row + [term_id, subject_id, category_id, filepath])
                count += 1
            if not count:
                raise ValueError("CSV must contain at least one term")
    except BaseException as exc:
        Path(temp_path).unlink(missing_ok=True)
        if isinstance(exc, (csv.Error, UnicodeError)):
            raise ValueError("Invalid CSV format or encoding") from exc
        raise
    return temp_path
