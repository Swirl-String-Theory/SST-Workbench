@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (".venv\Scripts\python.exe" check_continuation_completeness.py) else (py -3 check_continuation_completeness.py)
exit /b %ERRORLEVEL%
