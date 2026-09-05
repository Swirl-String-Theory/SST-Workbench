@echo off
setlocal EnableExtensions
cd /d "%~dp0"
python shape_canonical_analysis.py --stage extended --nresample 300
exit /b %ERRORLEVEL%
