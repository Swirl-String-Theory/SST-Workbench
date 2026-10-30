@echo off
setlocal
cd /d "%~dp0"
py -3 audit_native_census_v012.py --zip "falsifier_census_v0.1.0_output.zip" --out "audited_v0.1.0_data"
exit /b %ERRORLEVEL%
