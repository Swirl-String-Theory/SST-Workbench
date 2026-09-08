@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli reveal --root . --campaign "outputs/confirmatory_stability/campaign" --blind "outputs/confirmatory_stability/blind" --out "outputs/confirmatory_stability/reveal" --config "config/preset_confirmatory_stability.json"
exit /b %errorlevel%
