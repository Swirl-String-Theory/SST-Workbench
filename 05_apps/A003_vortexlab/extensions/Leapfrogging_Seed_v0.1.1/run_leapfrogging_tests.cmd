@echo off
setlocal
cd /d "%~dp0"
python -m unittest discover -s tests -v
if errorlevel 1 (
  echo FAIL: Leapfrogging addon tests.
  exit /b 1
)
echo PASS: Leapfrogging seed checks. No time evolution certified.
endlocal
