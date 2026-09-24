@echo off
setlocal
cd /d "%~dp0"
call run_build_cpp.cmd
if errorlevel 1 exit /b %errorlevel%
python -m sst_thpcf.campaign --config configs\extended.json --backend native --root . --package
if errorlevel 1 exit /b %errorlevel%
