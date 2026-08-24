@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python -m py_compile run_knotplot_stage.py analyze_results.py
if errorlevel 1 exit /b %ERRORLEVEL%
python tests\selftest.py
exit /b %ERRORLEVEL%
