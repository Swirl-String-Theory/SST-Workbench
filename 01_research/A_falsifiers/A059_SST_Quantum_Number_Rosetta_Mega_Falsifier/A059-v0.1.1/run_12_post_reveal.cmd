@echo off
setlocal
call run_python.cmd -m mega.reveal_analysis
exit /b %ERRORLEVEL%
