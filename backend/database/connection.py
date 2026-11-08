from pathlib import Path
from sqlmodel import create_engine, Session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / "core" / ".env")
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL)
# of course echo=True is always nice for debugging


async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session
