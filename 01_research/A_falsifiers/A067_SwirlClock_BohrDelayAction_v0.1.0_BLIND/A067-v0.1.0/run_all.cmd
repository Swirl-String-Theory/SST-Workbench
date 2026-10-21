@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="SELFTEST" (
  python -m unittest discover -s tests -v
  if errorlevel 1 exit /b 1
  exit /b 0
)
if /I "%~1"=="REVEAL" (
  echo REVEAL DENIED: scientific gates G7-G9 unresolved. Private key is excluded from BLIND ZIP.
  exit /b 4
)
python src\run.py
if errorlevel 1 exit /b %errorlevel%
python src\make_report.py
exit /b %errorlevel%
