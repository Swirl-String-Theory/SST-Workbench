@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call _common.cmd
if errorlevel 1 exit /b 1
echo ============================================================
echo Kelvin-McFarlane analytic oracle
 echo ============================================================
"%PY%" -m sst_threaded_hole_falsifier.cli kelvin-oracle
exit /b %errorlevel%
