@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo [FAIL] Python not found in PATH.
  exit /b 1
)
python build_registry.py
if errorlevel 1 exit /b 1
python -m unittest discover -s tests -p "test_*.py" -v
if errorlevel 1 exit /b 1
echo [PASS] Registry data reproducibly built and validation gates passed.
endlocal
