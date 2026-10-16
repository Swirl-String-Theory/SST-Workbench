@echo off
setlocal
cd /d "%~dp0"
py -3 reconstruct_census_v011.py "ORIGINAL_falsifier_census_v0.1.0_output.zip" "reconstructed"
if errorlevel 1 exit /b %errorlevel%
py -3 test_reconstruct_census_v011.py
exit /b %errorlevel%
