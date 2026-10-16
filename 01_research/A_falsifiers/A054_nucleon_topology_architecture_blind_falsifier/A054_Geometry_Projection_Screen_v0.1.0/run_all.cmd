@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv || exit /b 1
)
".venv\Scripts\python.exe" -c "import numpy, reportlab" 2>nul || ".venv\Scripts\python.exe" -m pip install -r requirements.txt || exit /b 1
set OPENBLAS_NUM_THREADS=1
set OMP_NUM_THREADS=1
if /I "%~1"=="TEST" (
  ".venv\Scripts\python.exe" -m unittest discover -s tests -v
  exit /b %errorlevel%
)
if /I "%~1"=="REPORT" (
  ".venv\Scripts\python.exe" tools\build_report.py || exit /b 1
  exit /b 0
)
if /I "%~1"=="FULL" (
  ".venv\Scripts\python.exe" src\screen.py --profile FULL --output results\FULL || exit /b 1
  ".venv\Scripts\python.exe" src\reference_overlays.py || exit /b 1
  ".venv\Scripts\python.exe" tools\build_report.py || exit /b 1
  exit /b 0
)
if /I "%~1"=="RESUME" (
  ".venv\Scripts\python.exe" src\screen.py --profile FULL --output results\FULL --resume || exit /b 1
  ".venv\Scripts\python.exe" src\reference_overlays.py || exit /b 1
  ".venv\Scripts\python.exe" tools\build_report.py || exit /b 1
  exit /b 0
)
".venv\Scripts\python.exe" src\screen.py --profile BASIC --output results\BASIC
exit /b %errorlevel%
