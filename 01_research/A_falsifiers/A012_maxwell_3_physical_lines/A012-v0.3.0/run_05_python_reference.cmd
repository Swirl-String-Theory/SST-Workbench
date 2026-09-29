@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
echo [3_MAXWELL] Running synthetic pure-Python reference tests...
"%PY%" -m pytest -q tests -k "not pklsa_live"
exit /b %errorlevel%
