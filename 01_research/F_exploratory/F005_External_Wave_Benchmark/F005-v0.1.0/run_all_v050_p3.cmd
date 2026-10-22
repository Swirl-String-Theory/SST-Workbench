@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist "data\f005_euler_v050.py" (
  echo ERROR: Required base F005 v0.5.0 solver data\f005_euler_v050.py not found.
  exit /b 2
)
if /I "%~1"=="TEST" goto tests
py -3 -m unittest discover -s tests -p "test_v050_p3.py" -v
if errorlevel 1 exit /b %errorlevel%
if /I "%~1"=="DEMO" (
  py -3 data\f005_v050_p3.py --root . --demo --out outputs\f005_conditional_euler_v0.5.0_p3_DEMO
  exit /b %errorlevel%
)
py -3 data\f005_v050_p3.py --root . --out outputs\f005_conditional_euler_v0.5.0_p3
exit /b %errorlevel%
:tests
py -3 -m unittest discover -s tests -p "test_v050_p3.py" -v
exit /b %errorlevel%
