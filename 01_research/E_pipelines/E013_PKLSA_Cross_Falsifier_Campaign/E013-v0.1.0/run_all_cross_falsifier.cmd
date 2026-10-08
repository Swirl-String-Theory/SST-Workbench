@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem E011 PKLSA Cross-Falsifier Campaign
rem Usage:
rem   run_all_cross_falsifier.cmd PLAN    C:\workspace\projects\SST-Workbench
rem   run_all_cross_falsifier.cmd BASIC   C:\workspace\projects\SST-Workbench
rem   run_all_cross_falsifier.cmd FULL    C:\workspace\projects\SST-Workbench
rem   run_all_cross_falsifier.cmd CERTIFY C:\workspace\projects\SST-Workbench

set "PROFILE=%~1"
if not defined PROFILE set "PROFILE=FULL"

if /I not "%PROFILE%"=="PLAN" if /I not "%PROFILE%"=="BASIC" if /I not "%PROFILE%"=="FULL" if /I not "%PROFILE%"=="CERTIFY" (
  echo [ERROR] Unknown profile "%PROFILE%".
  echo         Allowed: PLAN BASIC FULL CERTIFY
  exit /b 2
)

set "SST_WORKBENCH_ROOT=%~2"
if defined SST_WORKBENCH_ROOT goto :root_ok

set "PROBE=%~dp0"
:find_root
if exist "%PROBE%\.sst-workbench-root" (
  set "SST_WORKBENCH_ROOT=%PROBE%"
  goto :root_ok
)
for %%I in ("%PROBE%\..") do set "PARENT=%%~fI"
if /I "%PARENT%"=="%PROBE%" goto :no_root
set "PROBE=%PARENT%"
goto :find_root

:no_root
echo [ERROR] SST-Workbench root not found.
echo         Pass it explicitly:
echo         run_all_cross_falsifier.cmd %PROFILE% C:\workspace\projects\SST-Workbench
exit /b 2

:root_ok
for %%I in ("%SST_WORKBENCH_ROOT%") do set "SST_WORKBENCH_ROOT=%%~fI"

set "HERE=%~dp0"
set "CONFIG=%HERE%config\cross_falsifier_campaign.json"
set "TOPOLOGIES=%HERE%config\selected_topologies.json"
set "RUNNER=%HERE%tools\run_cross_falsifier.py"

if not exist "%CONFIG%" (
  echo [ERROR] Missing config: "%CONFIG%"
  exit /b 2
)
if not exist "%TOPOLOGIES%" (
  echo [ERROR] Missing topology manifest: "%TOPOLOGIES%"
  exit /b 2
)
if not exist "%RUNNER%" (
  echo [ERROR] Missing orchestrator: "%RUNNER%"
  exit /b 2
)

if not defined SST_NATIVE_THREADS set "SST_NATIVE_THREADS=16"

set "PYEXE="
where py >nul 2>&1
if not errorlevel 1 set "PYEXE=py -3"
if not defined PYEXE (
  where python >nul 2>&1
  if not errorlevel 1 set "PYEXE=python"
)
if not defined PYEXE (
  echo [ERROR] Python 3 was not found on PATH.
  exit /b 2
)

echo.
echo ============================================================
echo  E011 PKLSA Cross-Falsifier Campaign
echo  Profile        : %PROFILE%
echo  Workbench root : %SST_WORKBENCH_ROOT%
echo  Native threads : %SST_NATIVE_THREADS%
echo ============================================================
echo.

%PYEXE% "%RUNNER%" ^
  --profile "%PROFILE%" ^
  --workbench-root "%SST_WORKBENCH_ROOT%" ^
  --campaign-config "%CONFIG%" ^
  --topology-manifest "%TOPOLOGIES%"

set "RC=%ERRORLEVEL%"
echo.
if "%RC%"=="0" (
  echo [E011] Cross-falsifier orchestration completed.
) else (
  echo [E011] Cross-falsifier orchestration finished with infrastructure/runtime status %RC%.
)
exit /b %RC%
