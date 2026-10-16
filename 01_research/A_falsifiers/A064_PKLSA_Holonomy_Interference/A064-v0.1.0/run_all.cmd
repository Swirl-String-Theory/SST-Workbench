@echo off
setlocal
cd /d "%~dp0"
if not defined SST_FALSIFIER_FRAMEWORK_ROOT set "SST_FALSIFIER_FRAMEWORK_ROOT=%~dp0..\..\..\..\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.7"
if not exist "%SST_FALSIFIER_FRAMEWORK_ROOT%\CANONICAL_FREEZE.json" (
  echo ERROR: v1.0.7 CANONICAL_FREEZE.json not found at %SST_FALSIFIER_FRAMEWORK_ROOT%
  echo Set SST_FALSIFIER_FRAMEWORK_ROOT to the installed v1.0.7 root.
  exit /b 2
)
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv || exit /b 10
)
set "PY=.venv\Scripts\python.exe"
"%PY%" -m pip install -r requirements.txt || exit /b 11
"%PY%" src\verify_framework.py || exit /b 2
"%PY%" -m pytest tests -q || exit /b 3
"%PY%" src\runner.py --order 4 || exit /b 4
"%PY%" src\render_report.py || exit /b 5
"%PY%" src\package.py || exit /b 6
exit /b 0