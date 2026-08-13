@echo off
setlocal
cd /d "%~dp0"
call "cmd\09_RUN_DIRECTOR_CONVERGENCE.cmd"
exit /b %errorlevel%
