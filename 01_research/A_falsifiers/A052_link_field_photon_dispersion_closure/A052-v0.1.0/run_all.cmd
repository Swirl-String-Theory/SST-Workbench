@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "OUT=outputs"
set "BLINDZIP=..\A052_Link_Field_Photon_Dispersion_Closure_Falsifier_v0.1.0-outputs_BLIND.zip"
set "REVEALZIP=..\A052_Link_Field_Photon_Dispersion_Closure_Falsifier_v0.1.0-outputs_REVEALED.zip"

echo [A052] Preflight...
for %%F in (
  "configs\blind_config.json"
  "configs\reveal_config.json"
  "data\public\admissibility.json"
  "data\public\E010_PKLSA_v0.3.1_RELEASE.json"
  "data\public\E010_PKLSA_v0.3.1_RUN_CONTEXT.json"
  "data\public\E010_PKLSA_v0.3.1_CAMPAIGN_INDEX.json"
) do (
  if not exist "%%~F" (
    echo [A052][ERROR] Missing required input: %%~F
    echo [A052][ERROR] The local A052 folder is incomplete. Sync/download the complete A052-v0.1.0 folder before running.
    exit /b 2
  )
)

echo [A052] Python environment...
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto :fail
)
call .venv\Scripts\activate.bat
if errorlevel 1 goto :fail

python -m pip install --upgrade pip
if errorlevel 1 goto :fail
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo [A052] Tests...
python -m pytest -q
if errorlevel 1 goto :fail

echo [A052] Blind + reveal campaign...
python -m a052_lfpdcf.run --mode all --root . --outputs "%OUT%"
if errorlevel 1 goto :fail

if not exist "%OUT%\blind\verdict.json" (
  echo [A052][ERROR] Blind verdict was not produced.
  exit /b 3
)
if not exist "%OUT%\revealed\verdict.json" (
  echo [A052][ERROR] Reveal verdict was not produced.
  exit /b 3
)

echo [A052] Packaging outputs...
powershell -NoProfile -Command "if(Test-Path '%BLINDZIP%'){Remove-Item '%BLINDZIP%' -Force}; Compress-Archive -Path '%OUT%\blind\*' -DestinationPath '%BLINDZIP%' -Force"
if errorlevel 1 goto :fail
powershell -NoProfile -Command "if(Test-Path '%REVEALZIP%'){Remove-Item '%REVEALZIP%' -Force}; Compress-Archive -Path '%OUT%\revealed\*' -DestinationPath '%REVEALZIP%' -Force"
if errorlevel 1 goto :fail

echo.
echo [A052] PASS - campaign completed.
echo [A052] Read: %OUT%\revealed\verdict.json
exit /b 0

:fail
echo.
echo [A052][ERROR] Command failed. Aborting; outputs were not certified as a complete run.
exit /b 1
