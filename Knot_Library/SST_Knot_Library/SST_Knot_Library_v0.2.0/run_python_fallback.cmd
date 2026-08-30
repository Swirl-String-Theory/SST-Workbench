@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Knot Library v0.2.0 - Python fallback
 echo ============================================================
if not exist .venv py -3 -m venv .venv || exit /b 1
call .venv\Scripts\activate.bat || exit /b 1
python -m pip install --upgrade pip || exit /b 1
python -m pip install "numpy>=2.0" || exit /b 1
set PYTHONPATH=%CD%
python tests\test_smoke.py || exit /b 1
if not exist outputs mkdir outputs
python tests\validate_reference_cases.py > outputs\reference_validation_python.json || exit /b 1
python examples\make_seed_suite.py || exit /b 1
echo PASS: Python fallback validation completed.
