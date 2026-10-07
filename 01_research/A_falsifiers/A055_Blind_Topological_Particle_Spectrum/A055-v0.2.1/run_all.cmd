@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set PRESET=%~1
if "%PRESET%"=="" set PRESET=quick
set WB=%~2
if "%WB%"=="" set WB=C:\workspace\projects\SST-Workbench
if /I not "%PRESET%"=="quick" if /I not "%PRESET%"=="full" (
  echo Usage: run_all.cmd [quick^|full] [SST-Workbench-root]
  exit /b 2
)
echo [1/8] install
call run_00_install.cmd || exit /b 1
echo [2/8] build A055 topology-baseline C++ kernel
call run_05_build_cpp.cmd || exit /b 1
echo [3/8] package selftest
.venv\Scripts\python.exe -m a055_spectrum.cli selftest || exit /b 1
echo [4/8] STRICT C006 native build/import/parity preflight
call run_15_c006_native_preflight.cmd %PRESET% "%WB%" || exit /b 1
echo [5/8] BLIND E011/C006 dynamic campaign
call run_20_blind.cmd %PRESET% "%WB%" || exit /b 1
echo [6/8] seal BLIND tree
call run_30_seal.cmd %PRESET% || exit /b 1
echo [7/8] reveal historical + SM/Higgs mass-pattern layers
call run_40_reveal.cmd %PRESET% || exit /b 1
echo [8/8] package outputs
call run_50_package.cmd %PRESET% || exit /b 1
echo A055 v0.2.1 %PRESET% complete.
