@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
if exist "outputs\kelvin_hole_extended" rmdir /s /q "outputs\kelvin_hole_extended"
"%PY%" -m sst_threaded_hole_falsifier.cli prepare --root . --out "outputs\kelvin_hole_extended\campaign" --config "config\preset_kelvin_hole_extended.json"
exit /b %errorlevel%
