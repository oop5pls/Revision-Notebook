import csv
import magic


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
