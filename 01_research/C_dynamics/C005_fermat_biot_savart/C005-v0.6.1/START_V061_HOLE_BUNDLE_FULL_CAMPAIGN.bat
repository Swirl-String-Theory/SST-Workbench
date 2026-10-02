@echo off
setlocal
cd /d "%~dp0"
py -3 run_v061_campaign.py --preset full --require-native --overwrite --out-root v0.6.1_campaign_output --archive SST_fermat_pybind_research_v0.6.1_results.zip
set RC=%ERRORLEVEL%
echo.
echo v0.6.1 full-range native campaign exit code: %RC%
pause
exit /b %RC%
