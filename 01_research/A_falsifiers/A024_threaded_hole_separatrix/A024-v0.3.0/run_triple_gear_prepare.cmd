@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\triple_gear" rmdir /s /q "outputs\triple_gear"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/triple_gear/campaign" --config "config/preset_triple_gear.json"
exit /b %errorlevel%
