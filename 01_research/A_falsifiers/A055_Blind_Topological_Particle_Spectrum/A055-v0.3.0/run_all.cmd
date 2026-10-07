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
echo [1/9] install
call run_00_install.cmd || exit /b 1
echo [2/9] build A055 topology/control C++ kernel
call run_05_build_cpp.cmd || exit /b 1
echo [3/9] package selftest
.venv\Scripts\python.exe -m a055_spectrum.cli selftest || exit /b 1
echo [4/9] STRICT C006 native build/import/parity preflight
call run_15_c006_native_preflight.cmd %PRESET% "%WB%" || exit /b 1
echo [5/9] ensure authoritative A054 compound certification
call run_12_a054_compound_preflight.cmd %PRESET% "%WB%" || exit /b 1
echo [6/9] BLIND integrated S-branch + A054 C-branch
call run_20_blind.cmd %PRESET% "%WB%" || exit /b 1
echo [7/9] seal integrated BLIND tree
call run_30_seal.cmd %PRESET% || exit /b 1
echo [8/9] reveal compound architecture + historical hypotheses
call run_40_reveal.cmd %PRESET% || exit /b 1
echo [9/9] package outputs
call run_50_package.cmd %PRESET% || exit /b 1
echo A055 v0.3.0 %PRESET% complete.
