@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\similarity" rmdir /s /q "outputs\similarity"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/similarity/campaign" --config "config/preset_similarity.json"
exit /b %errorlevel%
