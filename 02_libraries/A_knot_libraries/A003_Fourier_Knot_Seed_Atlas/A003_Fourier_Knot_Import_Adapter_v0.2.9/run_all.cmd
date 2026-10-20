@echo off
setlocal EnableExtensions
set "ADAPTER_ROOT=%~dp0"
if /I "%~1"=="G6" goto G6
if /I "%~1"=="COMPLETE" goto COMPLETE
if /I "%~1"=="QUALIFY" goto QUALIFY
if /I "%~1"=="FULL" goto FULL
if /I "%~1"=="DIAGNOSTIC" goto DIAGNOSTIC
goto AUDIT
:G6
call "%ADAPTER_ROOT%run_g6_pklsa.cmd"
exit /b %ERRORLEVEL%
:COMPLETE
rem Execute G5 and G6 independently. G6 must run even if G5 science FAILs.
call "%ADAPTER_ROOT%run_g5_qualification.cmd"
set "G5_EXIT=%ERRORLEVEL%"
if "%G5_EXIT%"=="4" exit /b 4
call "%ADAPTER_ROOT%run_g6_pklsa.cmd"
set "G6_EXIT=%ERRORLEVEL%"
echo A003 COMPLETE: G5 exit %G5_EXIT%, G6 exit %G6_EXIT%.
if not "%G5_EXIT%"=="0" exit /b %G5_EXIT%
exit /b %G6_EXIT%
:QUALIFY
call "%ADAPTER_ROOT%run_g5_qualification.cmd"
exit /b %ERRORLEVEL%
:FULL
call "%ADAPTER_ROOT%run_all.cmd"
if errorlevel 1 exit /b 1
call "%ADAPTER_ROOT%run_g5_qualification.cmd"
exit /b %ERRORLEVEL%
:DIAGNOSTIC
call "%ADAPTER_ROOT%run_g5_diagnostic.cmd"
exit /b %ERRORLEVEL%
:AUDIT
set "ATLAS_ROOT=%ADAPTER_ROOT%..\A003-v0.1.2"
if defined SST_ATLAS_ROOT set "ATLAS_ROOT=%SST_ATLAS_ROOT%"
if not "%~1"=="" set "ATLAS_ROOT=%~1"
if not exist "%ATLAS_ROOT%\manifest.json" (
  echo FAIL_CLOSED: Atlas ontbreekt: "%ATLAS_ROOT%\manifest.json" 1>&2
  exit /b 2
)
set "SST_ATLAS_ROOT=%ATLAS_ROOT%"
rem Explicit hypothesis only: a_star is a dimensionless source-coordinate core radius.
set "A_STAR=0.05"
if defined SST_A003_REFERENCE_CORE_RADIUS_UNITS set "A_STAR=%SST_A003_REFERENCE_CORE_RADIUS_UNITS%"
if defined SST_A003_A_STAR set "A_STAR=%SST_A003_A_STAR%"
if not "%~2"=="" set "A_STAR=%~2"
echo A003 G4 ASSUMPTION ONLY: a_star=%A_STAR% source coordinate units.
if /I "%SST_A003_RUN_G5%"=="1" (
  echo G5 independent determinant screen requested; numerical evidence is NOT full certification.
  python "%ADAPTER_ROOT%fourier_atlas_adapter.py" --atlas "%ATLAS_ROOT%" --out "%ADAPTER_ROOT%outputs" --reference-core-radius-units "%A_STAR%" --g5 --g5-resolutions BASIC --require-g5-evidence catalog
) else (
  echo G5 topology screen NOT_RUN; use run_g5.cmd explicitly or SST_A003_RUN_G5=1.
  python "%ADAPTER_ROOT%fourier_atlas_adapter.py" --atlas "%ATLAS_ROOT%" --out "%ADAPTER_ROOT%outputs" --reference-core-radius-units "%A_STAR%" catalog
)
if errorlevel 1 exit /b 2
python -m unittest discover -s "%ADAPTER_ROOT%tests" -v
if errorlevel 1 exit /b 1
echo A003_v0.2.9_GEOMETRY_QUALIFIED / G4_CONDITIONAL_ONLY / G5Q_4LEVEL_OPT_IN / G6_NOT_RUN
exit /b 0
