@echo off
setlocal
cd /d "%~dp0"
call run_python.cmd tools\run_knotplot_campaign.py --tier pilot --exe "%~1" --workdir "%~2"
exit /b %ERRORLEVEL%
