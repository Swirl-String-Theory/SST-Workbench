@echo off
call .venv\Scripts\activate.bat || exit /b 1
pytest -q || exit /b 1
