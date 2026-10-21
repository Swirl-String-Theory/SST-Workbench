@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set OUT=SST_Cosmic_Gamma_Transparency_Dispersion_Lorentz_Emergence_Falsifier_v0.2.0-outputs
if not exist .venv\Scripts\python.exe (
  echo [1/7] Creating venv
  py -3 -m venv .venv || exit /b 1
)
call .venv\Scripts\activate.bat

echo [2/7] Installing dependencies
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt || exit /b 1

echo [3/7] Installing package / native backend
python -m pip install -q -e . || exit /b 1

echo [4/7] Running tests
pytest -q || exit /b 1

echo [5/7] Running blind campaign
python -m sst_cgtdlef.run || exit /b 1
python tools\audit_blind.py "%OUT%\blind" || exit /b 1

echo [6/7] Optional reveal
if exist private\candidate.json (
  python tools\verify_commitment.py private\candidate.json
  if errorlevel 1 (
    echo Reveal skipped or commitment invalid.
  ) else (
    python -m sst_cgtdlef.run --candidate private\candidate.json || exit /b 1
  )
) else (
  echo No private\candidate.json: SST closure remains OPEN by design.
)

echo [7/7] Packaging outputs
powershell -NoProfile -ExecutionPolicy Bypass -Command "if(Test-Path '..\%OUT%_BLIND.zip'){Remove-Item '..\%OUT%_BLIND.zip' -Force}; Compress-Archive -Path '%OUT%\blind\*' -DestinationPath '..\%OUT%_BLIND.zip' -Force"
if exist "%OUT%\revealed" powershell -NoProfile -ExecutionPolicy Bypass -Command "if(Test-Path '..\%OUT%_REVEALED.zip'){Remove-Item '..\%OUT%_REVEALED.zip' -Force}; Compress-Archive -Path '%OUT%\revealed\*' -DestinationPath '..\%OUT%_REVEALED.zip' -Force"
echo Done.
endlocal
