@echo off
setlocal
cd /d "%~dp0"
set "REPO=%CD%"
if not exist "%REPO%\.sst-workbench-root" (
  if exist "%CD%\..\.sst-workbench-root" (
    for %%I in ("%CD%\..") do set "REPO=%%~fI"
  )
)
if not exist "%REPO%\.sst-workbench-root" (
  echo ERROR: Could not locate SST-Workbench root.
  echo Extract this patch directly inside C:\workspace\projects\SST-Workbench\
  exit /b 2
)
where py >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python launcher "py" not found.
  exit /b 2
)
py -m pip install -r "%CD%\requirements-patch.txt"
if errorlevel 1 exit /b %errorlevel%

echo.
echo WARNING: This will modify FAMILY.yaml files and replace root falsifier_registry.yaml.
echo Backups will be created under:
echo   %REPO%\10_docs\migration\registry_evidence_patch_v0.1.0\backups\
echo.
set /p CONFIRM=Type APPLY to continue: 
if /I not "%CONFIRM%"=="APPLY" (
  echo Cancelled.
  exit /b 1
)
py "%CD%\scripts\mega_patch.py" --repo "%REPO%" --apply
exit /b %errorlevel%
