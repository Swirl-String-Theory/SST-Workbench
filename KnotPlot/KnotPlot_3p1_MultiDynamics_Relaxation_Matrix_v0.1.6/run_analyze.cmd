@echo off
setlocal
cd /d "%~dp0"
python analyze_matrix_effects.py %*
exit /b %ERRORLEVEL%
