@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call 5_env.cmd
if errorlevel 1 exit /b %errorlevel%
"%M5_PY%" -m maxwell5_native.build_ext_if_needed --strict || exit /b 3
"%M5_PY%" tests\run_tests.py
exit /b %errorlevel%
