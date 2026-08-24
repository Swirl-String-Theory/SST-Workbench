@echo off
setlocal
cd /d "%~dp0"
echo Full 10k smoke of B00 on both trefoil embeddings.
".venv\Scripts\python.exe" run_campaign.py --smoke-two-variants
exit /b %ERRORLEVEL%
