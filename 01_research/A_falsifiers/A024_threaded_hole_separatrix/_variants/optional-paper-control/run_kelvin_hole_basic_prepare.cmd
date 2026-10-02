@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\kelvin_hole_basic" rmdir /s /q "outputs\kelvin_hole_basic"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs\kelvin_hole_basic\campaign" --config "config\preset_kelvin_hole_basic.json"
exit /b %errorlevel%
