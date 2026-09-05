@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (".venv\Scripts\python.exe" apply_v0324_runtime_hotfix.py) else (py -3 apply_v0324_runtime_hotfix.py)
exit /b %ERRORLEVEL%
