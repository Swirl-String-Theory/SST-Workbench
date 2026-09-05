@echo off
setlocal
cd /d "%~dp0"
if exist analysis\EXTENDED_SKIPPED.flag exit /b 0
".venv\Scripts\python.exe" analyze.py extended
exit /b %ERRORLEVEL%
