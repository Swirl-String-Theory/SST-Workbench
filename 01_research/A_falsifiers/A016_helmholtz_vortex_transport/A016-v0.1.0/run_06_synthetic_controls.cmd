@echo off
setlocal EnableExtensions
call "%~dp0_paths.cmd"
cd /d "%ROOT%"
if not exist "%PY%" (echo [ERROR] Run run_00_install.cmd first.& exit /b 1)
"%PY%" make_synthetic_controls.py --out synthetic_controls
if errorlevel 1 exit /b %errorlevel%
"%PY%" -m pytest -q tests\test_controls.py
exit /b %ERRORLEVEL%
