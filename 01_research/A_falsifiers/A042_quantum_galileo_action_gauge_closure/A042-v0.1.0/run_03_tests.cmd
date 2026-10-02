@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo [3/7] Regression tests
echo ============================================================
call .venv\Scripts\activate.bat
set PYTHONPATH=%CD%
python -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
endlocal
