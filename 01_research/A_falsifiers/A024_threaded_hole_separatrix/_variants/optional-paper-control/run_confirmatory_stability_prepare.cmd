@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\confirmatory_stability" rmdir /s /q "outputs\confirmatory_stability"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/confirmatory_stability/campaign" --config "config/preset_confirmatory_stability.json"
exit /b %errorlevel%
