@echo off
setlocal EnableExtensions
set ROOT=%~1
if "%ROOT%"=="" set ROOT=..\..\Katlas_Sources_v0.2.2_Outputs
set OUT=%~2
if "%OUT%"=="" set OUT=outputs\Katlas_Conditioned_v2
call run_setup.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
if not exist outputs mkdir outputs
python -m sst_katlas_conditioning.cli scan "%ROOT%" --out outputs\SOURCE_SCAN.json || exit /b 1
python -m sst_katlas_conditioning.cli all "%ROOT%" "%OUT%" --config config\basic.json || exit /b 1
