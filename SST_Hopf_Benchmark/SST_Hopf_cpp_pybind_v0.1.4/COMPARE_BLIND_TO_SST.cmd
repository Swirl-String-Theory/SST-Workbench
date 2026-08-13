@echo off
setlocal
cd /d "%~dp0"
call "RUN_SST_REVEAL.cmd"
exit /b %errorlevel%
