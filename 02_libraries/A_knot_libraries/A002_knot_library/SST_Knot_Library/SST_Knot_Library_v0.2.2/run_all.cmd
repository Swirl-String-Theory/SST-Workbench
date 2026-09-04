@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo SST Knot Library v0.2.2 - full validation
echo ============================================================
if not exist .venv (
  echo [1/10] Creating virtual environment...
  py -3 -m venv .venv || goto :fail
) else echo [1/10] Virtual environment exists.
call .venv\Scripts\activate.bat || goto :fail

echo [2/10] Installing/updating core build dependencies...
python -m pip install --upgrade pip setuptools wheel >nul || goto :fail
python -m pip install -r requirements.txt || goto :fail

echo [3/10] Building/installing C++17 pybind11 backend...
python -m pip install -e . --no-build-isolation || goto :fail

if not exist outputs mkdir outputs

echo [4/10] Verifying release file integrity...
python -m sst_knotlib verify-integrity --require-pass > outputs\integrity_validation.json || goto :fail

echo [5/10] Runtime/release attestation + native/OpenMP requirement...
python -m sst_knotlib runtime-info --out outputs\runtime_validation.json --require-native --require-openmp --require-release-match || goto :fail
python -m sst_knotlib providers > outputs\provider_status.json || goto :fail
python -m sst_knotlib sources > outputs\source_catalog_validation.json || goto :fail

echo [6/10] Core unit/format/topology safety tests...
python tests\test_smoke.py || goto :fail
python -m sst_knotlib registry > outputs\katlas_registry_validation.json || goto :fail

echo [7/10] Reference geometry + braid validation...
python tests\validate_reference_cases.py > outputs\reference_validation.json || goto :fail
python examples\make_seed_suite.py || goto :fail

echo [8/10] Building and verifying blind track-trefoil campaign...
python -m sst_knotlib campaign configs\track_trefoil_seed_sweep.json --outdir outputs\blind_track_trefoil_campaign || goto :fail
python -m sst_knotlib verify-campaign outputs\blind_track_trefoil_campaign --require-private > outputs\blind_campaign_verification.json || goto :fail

echo [9/10] Creating topology-controlled independent reference seeds...
python -m sst_knotlib seed-from-topology 3_1 --method braid --out outputs\katlas_braid_3_1.xyz || goto :fail
python -m sst_knotlib seed-from-topology 4_1 --method braid --out outputs\katlas_braid_4_1.xyz || goto :fail
python -m sst_knotlib seed-from-topology 6_2 --method braid --out outputs\katlas_braid_6_2.xyz || goto :fail
python -m sst_knotlib seed-from-topology 7_4 --method braid --out outputs\katlas_braid_7_4.xyz || goto :fail

echo [10/10] Trust-layer sanity complete.
echo.
echo PASS: release identity, native backend, registry, source catalog, formats, references and blind campaign completed.
echo Optional topology packages are NOT required; see outputs\provider_status.json.
echo Outputs: %CD%\outputs
exit /b 0
:fail
echo.
echo FAIL: command returned errorlevel %errorlevel%.
exit /b 1
