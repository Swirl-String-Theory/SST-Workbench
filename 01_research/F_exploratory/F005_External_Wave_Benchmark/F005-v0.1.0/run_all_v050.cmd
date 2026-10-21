@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="DEMO" (
  py -3 -m unittest discover -s tests -p "test_v050*.py" -v || exit /b 1
  py -3 data\f005_euler_v050.py --root . --demo --output outputs\f005_independent_euler_v0.5.0_DEMO
  exit /b %ERRORLEVEL%
)
py -3 -m unittest discover -s tests -p "test_v050*.py" -v || exit /b 1
py -3 data\f005_euler_v050.py --root . --geometry config\EULER_GEOMETRY_REQUIRED.json --output outputs\f005_independent_euler_v0.5.0
exit /b %ERRORLEVEL%
