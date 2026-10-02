@echo off
setlocal
set OLDOUT=%~1
if "%OLDOUT%"=="" set OLDOUT=..\SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.1.0\outputs\basic
set CFG=%~2
if "%CFG%"=="" set CFG=config\basic.json

echo ============================================================
echo SST Trefoil Dynamic Seed Qualification Mega Falsifier v0.1.1
echo Resume existing S10-S40 campaign at S50
echo Existing output: %OLDOUT%
echo Config:          %CFG%
echo ============================================================

if not exist "%OLDOUT%\stage40_long\results.json" (
  echo ERROR: stage40_long\results.json not found under %OLDOUT%
  exit /b 2
)

call run_00_setup.cmd || exit /b 1
call run_01_build_native.cmd || exit /b 1
call run_02_selftest.cmd || exit /b 1

if exist "%OLDOUT%\stage50_rpo_floquet" rmdir /s /q "%OLDOUT%\stage50_rpo_floquet"
if exist "%OLDOUT%\stage60_finite_core_clock" rmdir /s /q "%OLDOUT%\stage60_finite_core_clock"
if exist "%OLDOUT%\BLIND_CHAIN_SUMMARY.json" del /q "%OLDOUT%\BLIND_CHAIN_SUMMARY.json"
if exist "%OLDOUT%\REVEAL_SUMMARY.json" del /q "%OLDOUT%\REVEAL_SUMMARY.json"

call run_50_rpo.cmd "%OLDOUT%" "%CFG%" || exit /b 1
call run_60_mechanism.cmd "%OLDOUT%" "%CFG%" || exit /b 1
call run_70_reveal.cmd "%OLDOUT%" || exit /b 1

echo ============================================================
echo Resume complete.
echo Inspect: %OLDOUT%\stage50_rpo_floquet\summary.json
echo          %OLDOUT%\BLIND_CHAIN_SUMMARY.json
echo          %OLDOUT%\REVEAL_SUMMARY.json
echo ============================================================
