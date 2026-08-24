@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python run_knotplot_stage.py --stage cert
exit /b %ERRORLEVEL%
