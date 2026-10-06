@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

rem Run this script from inside A050-v0.3.0 after the broken overlay install.
rem It preserves v0.3.0 and creates sibling A050-v0.3.1.

set "SRC=%CD%"
for %%I in ("%SRC%") do set "SRCNAME=%%~nxI"
if /I not "%SRCNAME%"=="A050-v0.3.0" (
  echo [WARN] Current directory is "%SRCNAME%", expected A050-v0.3.0.
  echo        Continuing only if the required overlay files are present.
)

set "OVL=%SRC%\overlay"
set "DST=%SRC%\..\A050-v0.3.1"

if not exist "%OVL%\sst_gfcc_blind\nonstationary.py" (
  echo [ERROR] Missing overlay\sst_gfcc_blind\nonstationary.py
  echo         The broken patch overlay is incomplete.
  exit /b 2
)
if not exist "%OVL%\tests\test_v031.py" (
  echo [ERROR] Missing overlay\tests\test_v031.py
  exit /b 2
)
if not exist "%OVL%\config\SEAL_v0.3.1.json" (
  echo [ERROR] Missing overlay\config\SEAL_v0.3.1.json
  exit /b 2
)
if not exist "%OVL%\run_all.cmd" (
  echo [ERROR] Missing overlay\run_all.cmd
  echo         Refusing a partial promotion.
  exit /b 2
)

if exist "%DST%" (
  echo [ERROR] Destination already exists:
  echo         %DST%
  echo         Rename/remove that directory first; this script will not overwrite it.
  exit /b 3
)

echo [1/4] Copy pristine v0.3.0 base to sibling v0.3.1 ...
robocopy "%SRC%" "%DST%" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP ^
  /XD "%OVL%" "%SRC%\.venv" "%SRC%\.pytest_cache" "__pycache__" ^
      "%SRC%\SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.3.0-outputs" >nul
set "RC=%ERRORLEVEL%"
if %RC% GEQ 8 (
  echo [ERROR] Base copy failed, robocopy=%RC%
  exit /b %RC%
)

if exist "%DST%\overlay" rmdir /s /q "%DST%\overlay"
if exist "%DST%\.pytest_cache" rmdir /s /q "%DST%\.pytest_cache"

echo [2/4] Promote v0.3.1 overlay into sibling root ...
robocopy "%OVL%" "%DST%" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD "__pycache__" >nul
set "RC=%ERRORLEVEL%"
if %RC% GEQ 8 (
  echo [ERROR] Overlay promotion failed, robocopy=%RC%
  exit /b %RC%
)

echo [3/4] Structural checks ...
if not exist "%DST%\sst_gfcc_blind\nonstationary.py" (
  echo [ERROR] nonstationary.py did not reach the package root.
  exit /b 4
)
if not exist "%DST%\tests\test_v031.py" (
  echo [ERROR] test_v031.py did not reach tests root.
  exit /b 4
)
if not exist "%DST%\config\SEAL_v0.3.1.json" (
  echo [ERROR] SEAL_v0.3.1.json did not reach config root.
  exit /b 4
)
findstr /C:"A050 v0.3.1" "%DST%\run_all.cmd" >nul
if errorlevel 1 (
  echo [ERROR] Destination run_all.cmd is not v0.3.1.
  exit /b 4
)

findstr /C:"SEAL_v0.3.1.json" "%DST%\tools\preflight.py" >nul
if errorlevel 1 (
  echo [ERROR] Destination preflight.py is not v0.3.1.
  exit /b 4
)

echo [4/4] Import smoke test ...
pushd "%DST%"
call run_setup.cmd
if errorlevel 1 (
  popd
  echo [ERROR] run_setup.cmd failed.
  exit /b 5
)
call .venv\Scripts\activate.bat
python -c "from sst_gfcc_blind.nonstationary import phase_drift_from_series; print('IMPORT PASS: sst_gfcc_blind.nonstationary')"
if errorlevel 1 (
  popd
  echo [ERROR] v0.3.1 import smoke test failed.
  exit /b 6
)
python -m pytest -q tests\test_v031.py
if errorlevel 1 (
  popd
  echo [ERROR] v0.3.1 synthetic diagnostic tests failed.
  exit /b 7
)
popd

echo.
echo ============================================================
echo A050-v0.3.1 repair PASS
 echo Destination: %DST%
echo v0.3.0 was not modified.
echo.
echo Next:
echo   cd /d "%DST%"
echo   run_all.cmd C:\workspace\projects\SST-Workbench
echo ============================================================
exit /b 0
