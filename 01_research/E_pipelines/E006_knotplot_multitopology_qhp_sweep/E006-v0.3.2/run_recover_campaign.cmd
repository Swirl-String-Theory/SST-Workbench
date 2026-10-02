@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (echo Usage: run_recover_campaign.cmd campaign_name & exit /b 2)
if exist ".venv\Scripts\python.exe" (set PYEXE=.venv\Scripts\python.exe) else (set PYEXE=py -3)
%PYEXE% audit_campaign_integrity.py --campaign "campaigns\%~1"
if errorlevel 1 exit /b %ERRORLEVEL%
%PYEXE% recover_metrics_from_k.py --campaign "campaigns\%~1" --replace-analysis
exit /b %ERRORLEVEL%
