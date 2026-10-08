@echo off
setlocal
call run_python.cmd -m mega.phase_runner P08
exit /b %ERRORLEVEL%
