@echo off
setlocal
cd /d "%~dp0"
if not defined PYTHON set "PYTHON=python"
if "%~1"=="" goto HELP
"%PYTHON%" src\runner.py %*
exit /b %ERRORLEVEL%
:HELP
echo Usage: run_all.cmd PREPARE^|SELFTEST^|BASIC^|FULL^|STABILITY^|FEEDBACK^|MATRIX^|LOCK^|HOLDOUT^|REVEAL^|REPORT
exit /b 1
