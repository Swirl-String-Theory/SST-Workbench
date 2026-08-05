@echo off
setlocal
cd /d "%~dp0"
py -3 run_v061_campaign.py --preset smoke --force-python --overwrite --out-root v0.6.1_python_smoke_output --archive SST_fermat_pybind_research_v0.6.1_python_smoke_results.zip
set RC=%ERRORLEVEL%
echo.
echo v0.6.1 Python-fallback smoke campaign exit code: %RC%
pause
exit /b %RC%
