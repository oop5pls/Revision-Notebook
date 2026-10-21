from fastapi import APIRouter, UploadFile, File, Form
from backend.services.file_services import *
import os

import time

router = APIRouter(prefix="/file")


@router.post('/upload')
async def upload(
    file: UploadFile = File(...),
    category: str = Form(...),
    subject: str = Form(...)
):
    start_time = time.perf_counter()
    saved_path = await save_upload_file(file)

    try:
        with open(saved_path, 'rb') as f:
            if not validate_file_type(f, file.filename):
                raise ValueError("Unsupported file type")

        if saved_path.endswith('.csv'):
            await process_csv_to_db(saved_path, category, subject)
        elif saved_path.endswith('.xlsx') or saved_path.endswith('.xls'):
            await process_excel_to_db(saved_path)
        else:
            raise ValueError("Unsupported file extension")

        total_duration = time.perf_counter() - start_time
        print(f"[DEBUG] Total upload and processing time: {total_duration:.4f} seconds")
        return {
            "message": "File uploaded and processed successfully", 
            "path": saved_path,
        }
    except Exception as e:
        if os.path.exists(saved_path):
            os.remove(saved_path)
        print(e)
