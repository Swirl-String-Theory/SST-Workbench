@echo off
setlocal
cd /d "%~dp0"
call _common.cmd || exit /b 1
"%PY%" -m pytest
exit /b %errorlevel%
