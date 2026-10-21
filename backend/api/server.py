from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from backend.api import files_router

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI()

app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")
app.include_router(files_router.router)


@app.get("/")
async def home():
    return FileResponse(FRONTEND_DIR / "index.html")
