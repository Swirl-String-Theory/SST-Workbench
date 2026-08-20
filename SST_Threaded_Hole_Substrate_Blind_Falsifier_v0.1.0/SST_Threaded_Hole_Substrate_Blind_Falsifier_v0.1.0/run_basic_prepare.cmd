@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\basic" rmdir /s /q "outputs\basic"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs/basic/campaign" --config "config/preset_basic.json"
exit /b %errorlevel%
