@echo off
setlocal
call run_python.cmd -m mega.phase_runner P06
exit /b %ERRORLEVEL%
