@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "WORKBENCH=%~1"
if not defined WORKBENCH for %%I in ("%CD%\..\..\..\..") do set "WORKBENCH=%%~fI"

set "SOURCE=%CD%\patch_payload\knot.8_5.short"
set "TARGETDIR=%WORKBENCH%\03_data\A_knots\06_knot_library\Sources\FourierSeries_Fremlin\original\8_5"
set "TARGET=%TARGETDIR%\knot.8_5.short"
set "EXPECTED=8191f86a491a84c59ef677d07e95c038a90f908b8b925ed69739f9fdc6c27778"

if not exist "%SOURCE%" (
  echo [FAIL] Bundled source missing: %SOURCE%
  exit /b 2
)

for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath '%SOURCE%').Hash.ToLowerInvariant()"`) do set "SOURCEHASH=%%H"
if /I not "!SOURCEHASH!"=="%EXPECTED%" (
  echo [FAIL] Bundled knot.8_5.short SHA-256 mismatch.
  echo        Expected: %EXPECTED%
  echo        Actual  : !SOURCEHASH!
  exit /b 3
)

if not exist "%TARGETDIR%" mkdir "%TARGETDIR%"
if errorlevel 1 exit /b %errorlevel%

if exist "%TARGET%" (
  for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath '%TARGET%').Hash.ToLowerInvariant()"`) do set "TARGETHASH=%%H"
  if /I "!TARGETHASH!"=="%EXPECTED%" (
    echo [OK] Canonical Fremlin 8_5 .short already present with expected SHA-256.
    echo      %TARGET%
    exit /b 0
  )
  for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMddTHHmmss"`) do set "STAMP=%%T"
  set "BACKUP=%TARGET%.prepatch-!STAMP!.bak"
  copy /b /y "%TARGET%" "!BACKUP!" >nul
  if errorlevel 1 (
    echo [FAIL] Could not back up existing target.
    exit /b 4
  )
  echo [backup] Existing different file saved as:
  echo          !BACKUP!
)

copy /b /y "%SOURCE%" "%TARGET%" >nul
if errorlevel 1 (
  echo [FAIL] Could not install knot.8_5.short
  exit /b 5
)

for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath '%TARGET%').Hash.ToLowerInvariant()"`) do set "TARGETHASH=%%H"
if /I not "!TARGETHASH!"=="%EXPECTED%" (
  echo [FAIL] Installed file SHA-256 verification failed.
  exit /b 6
)

echo [OK] Installed Fremlin 8_5 .short geometry:
echo      %TARGET%
echo      SHA-256: %EXPECTED%
exit /b 0
