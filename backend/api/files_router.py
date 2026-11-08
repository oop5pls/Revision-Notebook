import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend.services.file_storage import save_upload_file, remove_upload
from backend.services.file_validation import validate_file_type
from backend.services.ingestion import process_csv_to_db, retry_file_index

router = APIRouter(prefix="/file")
logger = logging.getLogger(__name__)


@router.post('/upload')
async def upload(
    file: UploadFile = File(...),
    category: str = Form(...),
    subject: str = Form(...)
):
    saved_path = None
    try:
        if not category.strip() or not subject.strip():
            raise HTTPException(422, "Category and subject must not be blank")
        extension = Path(file.filename or "").suffix.lower()
        if extension in {".xlsx", ".xls"}:
            raise HTTPException(501, "Excel insertion is not implemented yet")
        if extension != ".csv":
            raise HTTPException(415, "Unsupported file extension")
        saved_path = await save_upload_file(file)
        try:
            with open(saved_path, "rb") as stream:
                validate_file_type(stream, file.filename or "")
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        result = await process_csv_to_db(saved_path, category, subject)
        return JSONResponse(status_code=202 if result["retryable"] else 200, content=result)
    except HTTPException:
        if saved_path:
            remove_upload(saved_path)
        raise
    except ValueError as exc:
        if saved_path:
            remove_upload(saved_path)
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        if saved_path:
            remove_upload(saved_path)
        logger.exception("Upload failed")
        raise HTTPException(500, "File processing failed") from exc
    finally:
        await file.close()


class IndexRetry(BaseModel):
    path: str


@router.post('/retry-index')
async def retry_index(request: IndexRetry):
    try:
        result = await retry_file_index(request.path)
    except LookupError as exc:
        raise HTTPException(404, "File not found in PostgreSQL") from exc
    return JSONResponse(status_code=202 if result["retryable"] else 200, content=result)
