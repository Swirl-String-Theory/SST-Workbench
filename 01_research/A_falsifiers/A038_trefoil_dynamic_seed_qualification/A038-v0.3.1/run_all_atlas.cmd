@echo off
setlocal EnableExtensions
call _common.cmd

set REPO=%~1
if "%REPO%"=="" for %%I in ("%~dp0..\..") do set REPO=%%~fI
set ROOTOUT=SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.1-outputs
set ATLAS=%~2
set OUT=%~3
if not "%OUT%"=="" for %%I in ("%OUT%\..") do set ROOTOUT=%%~fI
if "%OUT%"=="" if not "%ATLAS%"=="" for %%I in ("%ATLAS%\..") do set ROOTOUT=%%~fI
if "%ATLAS%"=="" set ATLAS=%ROOTOUT%\prospective_atlas
if "%OUT%"=="" set OUT=%ROOTOUT%\scientific_campaign
set CFG=config\prospective_atlas.json
set PROTOCOL=config\phase_b.json

if "%SST_KNOT_LIBRARY_HOME%"=="" set SST_KNOT_LIBRARY_HOME=%REPO%\Knot_Library\SST_Knot_Library\SST_Knot_Library_v0.2.5

echo ============================================================
echo SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.3.1
echo Pinned KnotRecord atlas + Phase B chain
echo Repository: %REPO%
echo Knot library: %SST_KNOT_LIBRARY_HOME%
echo Atlas: %ATLAS%
echo Campaign: %OUT%
echo ============================================================

if not exist "%SST_KNOT_LIBRARY_HOME%\RELEASE.json" (
  echo ERROR: pinned SST Knot Library v0.2.5 not found.
  echo Expected: %SST_KNOT_LIBRARY_HOME%
  exit /b 2
)
if exist "%ATLAS%" (
  echo ERROR: atlas output already exists; refusing overwrite: %ATLAS%
  exit /b 2
)
if exist "%OUT%" (
  echo ERROR: campaign output already exists; refusing overwrite: %OUT%
  exit /b 2
)

call run_00_setup.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_02_selftest.cmd || exit /b 1

call .venv\Scripts\activate.bat
python -m sst_seed_falsifier.knot_library verify --repo "%REPO%" --config "%CFG%" || exit /b 1
python -m sst_seed_falsifier.atlas freeze "%REPO%" "%ATLAS%" --config "%CFG%" --protocol "%PROTOCOL%" || exit /b 1
python -m sst_seed_falsifier.atlas generate-test "%REPO%" "%ATLAS%" || exit /b 1
python -u -m sst_seed_falsifier.campaign screen --repo "%REPO%" --atlas "%ATLAS%" --out "%OUT%" --config "%CFG%" || exit /b 1
python -u -m sst_seed_falsifier.campaign phase-b --repo "%REPO%" --atlas "%ATLAS%" --out "%OUT%" --config "%CFG%" --protocol "%PROTOCOL%" || exit /b 1
python -m sst_seed_falsifier.archive blind "%ROOTOUT%" || exit /b 1
python -m sst_seed_falsifier.campaign reveal --out "%OUT%" || exit /b 1
python -m sst_seed_falsifier.archive revealed "%ROOTOUT%" || exit /b 1

echo ============================================================
echo v0.3.1 chain complete.
echo Inspect:
echo   %ATLAS%\ATLAS_SUMMARY.json
echo   %OUT%\BLIND_CHAIN_SUMMARY.json
echo   %OUT%\PHASE_B_SUMMARY.json
echo   %OUT%\REVEAL_SUMMARY.json
echo ============================================================
exit /b 0
