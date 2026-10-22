@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if /I "%~1"=="TEST" goto tests
py -3 data\f005_v050_p2.py --root .
if errorlevel 1 exit /b %errorlevel%
exit /b 0
:tests
py -3 -m unittest discover -s tests -p test_v050_p2.py -v
exit /b %errorlevel%
