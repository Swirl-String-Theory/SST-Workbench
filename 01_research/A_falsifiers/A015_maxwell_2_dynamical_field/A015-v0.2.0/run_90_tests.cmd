@echo off
setlocal EnableExtensions
call "%~dp0_paths.cmd"
cd /d "%ROOT%"
if not exist "%PY%" (echo [ERROR] Run run_00_install.cmd first.& exit /b 1)
"%PY%" make_synthetic_controls.py
if errorlevel 1 exit /b %errorlevel%
"%PY%" tests\test_controls.py
if errorlevel 1 exit /b %errorlevel%
"%PY%" -m pytest -q
exit /b %ERRORLEVEL%
