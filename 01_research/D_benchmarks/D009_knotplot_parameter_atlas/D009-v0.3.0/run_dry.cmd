@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python tests\selftest.py
if errorlevel 1 exit /b %ERRORLEVEL%
python tests\test_shape_canonical.py
if errorlevel 1 exit /b %ERRORLEVEL%
python tests\test_sst_v048_bridge.py
exit /b %ERRORLEVEL%
