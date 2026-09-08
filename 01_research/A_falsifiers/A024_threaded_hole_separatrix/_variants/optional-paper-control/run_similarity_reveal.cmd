@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli reveal --root . --campaign "outputs/similarity/campaign" --blind "outputs/similarity/blind" --out "outputs/similarity/reveal" --config "config/preset_similarity.json"
exit /b %errorlevel%
