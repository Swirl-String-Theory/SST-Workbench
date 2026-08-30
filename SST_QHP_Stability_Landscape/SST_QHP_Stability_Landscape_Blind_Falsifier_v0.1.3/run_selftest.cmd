@echo off
setlocal
call .venv\Scripts\activate.bat
python -m sst_qhp_falsifier.cli selftest
if errorlevel 1 exit /b 1
python -m pytest tests -q
