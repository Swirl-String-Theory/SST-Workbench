@echo off
setlocal
cd /d "%~dp0"
echo Full 10k smoke of the first candidate only.
".venv\Scripts\python.exe" run_matrix.py --limit 1
exit /b %ERRORLEVEL%
