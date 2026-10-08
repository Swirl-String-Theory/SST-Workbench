@echo off
setlocal
call run_python.cmd -m mega.phase_runner P07
exit /b %ERRORLEVEL%
