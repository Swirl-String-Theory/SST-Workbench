@echo off
setlocal EnableExtensions
call "%~dp0_paths.cmd"
cd /d "%ROOT%"
if "%~1"=="" (echo Usage: run_04_reveal.cmd C:\path\to\frozen_result.json& exit /b 1)
"%PY%" reveal_targets.py "%~1"
exit /b %ERRORLEVEL%
