@echo off
set PYTHONPATH=%CD%
uv run fastapi dev backend/api/server.py
pause