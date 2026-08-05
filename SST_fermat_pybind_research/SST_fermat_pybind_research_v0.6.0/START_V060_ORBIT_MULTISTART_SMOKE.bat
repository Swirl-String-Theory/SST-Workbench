@echo off
setlocal
cd /d "%~dp0"
py -3 run_v060_campaign.py --preset smoke --overwrite --archive SST_fermat_pybind_research_v0.6.0_smoke_results.zip
set RC=%ERRORLEVEL%
echo.
echo v0.6.0 smoke exit code: %RC%
pause
exit /b %RC%
