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
echo [1/7] install
call run_00_install.cmd || exit /b 1
echo [2/7] build A055 topology-baseline C++ kernel
call run_05_build_cpp.cmd || exit /b 1
echo [3/7] selftest
.venv\Scripts\python.exe -m a055_spectrum.cli selftest || exit /b 1
echo [4/7] BLIND E011/C006 dynamic campaign
call run_20_blind.cmd %PRESET% "%WB%" || exit /b 1
echo [5/7] seal BLIND tree
call run_30_seal.cmd %PRESET% || exit /b 1
echo [6/7] reveal historical + SM/Higgs mass-pattern layers
call run_40_reveal.cmd %PRESET% || exit /b 1
echo [7/7] package outputs
call run_50_package.cmd %PRESET% || exit /b 1
echo A055 v0.2.0 complete.
