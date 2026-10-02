@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
"%PY%" -m sst_threaded_hole_falsifier.cli blind --root . --campaign "outputs\kelvin_hole_basic\campaign" --out "outputs\kelvin_hole_basic\blind" --config "config\preset_kelvin_hole_basic.json"
exit /b %errorlevel%
