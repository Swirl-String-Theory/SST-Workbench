@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python prepare_sst_stability_handoff.py
exit /b %ERRORLEVEL%
