@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Knot Geometry Library v0.1.0 - full validation
 echo ============================================================
if not exist .venv (
  echo [1/6] Creating virtual environment...
  py -3 -m venv .venv || goto :fail
) else echo [1/6] Virtual environment exists.
call .venv\Scripts\activate.bat || goto :fail

echo [2/6] Installing/updating build dependencies...
python -m pip install --upgrade pip setuptools wheel >nul || goto :fail
python -m pip install -r requirements.txt || goto :fail

echo [3/6] Building/installing C++17 pybind11 backend...
python -m pip install -e . --no-build-isolation || goto :fail

echo [4/6] Running unit tests...
python tests\test_smoke.py || goto :fail

echo [5/6] Running reference validation and seed suite...
if not exist outputs mkdir outputs
python tests\validate_reference_cases.py > outputs\reference_validation.json || goto :fail
python examples\make_seed_suite.py || goto :fail

echo [6/6] Building blind track-trefoil candidate campaign...
python -m sst_knotlib campaign configs\track_trefoil_seed_sweep.json --outdir outputs\blind_track_trefoil_campaign || goto :fail

echo.
echo PASS: library, native backend, tests, seed suite and blind campaign completed.
echo Outputs: %CD%\outputs
exit /b 0
:fail
echo.
echo FAIL: command returned errorlevel %errorlevel%.
exit /b 1
