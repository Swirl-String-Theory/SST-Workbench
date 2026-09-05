@echo off
setlocal
cd /d "%~dp0"
py -3 run_v060_campaign.py --preset full --require-native --overwrite --archive SST_fermat_pybind_research_v0.6.0_results.zip
set RC=%ERRORLEVEL%
echo.
echo v0.6.0 hole-bundle full campaign exit code: %RC%
pause
exit /b %RC%
