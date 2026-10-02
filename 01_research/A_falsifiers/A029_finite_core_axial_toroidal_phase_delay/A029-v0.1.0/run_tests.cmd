@echo off
call "%~dp0_common.cmd" || exit /b 1
cd /d "%ROOT%"
"%PY%" -m pytest -q
