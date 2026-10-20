@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist "data\f005_free_run_family_v0.4.1.py" (
  echo [F005 v0.4.2] Missing v0.4.1 dependency in data\
  exit /b 2
)
py -3 -m unittest discover -s tests -p test_f005_v042.py -v
if errorlevel 1 exit /b 2
py -3 "data\f005_qualification_v0.4.2.py" --root "%CD%" --verbose
if errorlevel 1 exit /b 2
echo [F005 v0.4.2] Development outputs generated. TEST/OOD responses remain sealed.
exit /b 0
