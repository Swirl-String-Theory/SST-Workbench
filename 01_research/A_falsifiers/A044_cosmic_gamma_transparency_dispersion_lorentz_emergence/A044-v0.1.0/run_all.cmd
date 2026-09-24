\
@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ============================================================
echo SST Cosmic Gamma Transparency / Dispersion Falsifier v0.1.0
echo ============================================================

echo [1/7] Create / update environment
if not exist ".venv\Scripts\python.exe" (
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if errorlevel 1 exit /b !errorlevel!
)
set "PY=.venv\Scripts\python.exe"
"%PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b !errorlevel!
"%PY%" -m pip install -r requirements.txt
if errorlevel 1 exit /b !errorlevel!

echo [2/7] Build native C++ / pybind11 backend
"%PY%" -m pip install -e . --no-build-isolation
if errorlevel 1 exit /b !errorlevel!

echo [3/7] Native and policy tests
"%PY%" -m pytest -q
if errorlevel 1 exit /b !errorlevel!

echo [4/7] BLIND campaign
"%PY%" -m sst_cgtdlef.run blind --config configs\blind_config.json
if errorlevel 1 exit /b !errorlevel!

echo [5/7] Blind leakage audit
if exist "private\forbidden_reveal_tokens.json" (
  "%PY%" tools\verify_blind_clean.py --root . --forbidden-file private\forbidden_reveal_tokens.json
) else (
  "%PY%" tools\verify_blind_clean.py --root .
)
if errorlevel 1 exit /b !errorlevel!

echo [6/7] REVEAL / SST closure
if exist "private\reveal_sst_constants.json" if exist "configs\reveal_config.json" (
  "%PY%" -m sst_cgtdlef.run reveal --config configs\reveal_config.json
  if errorlevel 1 exit /b !errorlevel!
) else (
  echo [INFO] Private reveal payload absent: BLIND-only release. Reveal skipped.
)

echo [7/7] Package shareable outputs
"%PY%" tools\package_outputs.py
if errorlevel 1 exit /b !errorlevel!

echo ============================================================
echo DONE
echo Results: .\SST_Cosmic_Gamma_Transparency_Dispersion_Lorentz_Emergence_Falsifier_v0.1.0-outputs\
echo Archives are written one directory above this project.
echo ============================================================
exit /b 0
