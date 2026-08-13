@echo off
setlocal
cd /d "%~dp0"
call "cmd\10_RUN_HIGHRES_HOPF.cmd"
exit /b %errorlevel%
