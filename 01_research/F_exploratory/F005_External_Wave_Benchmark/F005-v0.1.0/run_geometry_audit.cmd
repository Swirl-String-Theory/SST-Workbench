@echo off
setlocal
cd /d "%~dp0"
py -3 tests\test_camilotto_geometry.py
exit /b %ERRORLEVEL%
