@echo off
setlocal
cd /d "%~dp0"
set "WB=%SST_WORKBENCH_ROOT%"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
set "FAMILY=%WB%\06_templates\SST_Falsifier_Framework"
set "TARGET=%FAMILY%\SST_Falsifier_Framework_v1.0.6"
if exist "%TARGET%\sst_falsifier\__init__.py" (
  echo Framework v1.0.6 already present: %TARGET%
  exit /b 0
)
if not exist "%FAMILY%" mkdir "%FAMILY%"
echo Installing frozen framework reference into %FAMILY% ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath '%CD%\inputs\SST_Falsifier_Framework_v1.0.6-CANONICAL_FROZEN.zip' -DestinationPath '%FAMILY%' -Force"
if not exist "%TARGET%\sst_falsifier\__init__.py" (
  echo ERROR: framework extraction did not create expected target.
  exit /b 1
)
echo Framework installed: %TARGET%
exit /b 0
