@echo off
setlocal
call .venv\Scripts\activate.bat
python -m sst_modal_clock.cli selftest || exit /b 1
python -m pytest -q || exit /b 1
