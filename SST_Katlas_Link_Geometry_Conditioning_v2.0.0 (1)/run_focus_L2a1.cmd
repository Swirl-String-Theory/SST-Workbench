@echo off
setlocal EnableExtensions
set ROOT=%~1
if "%ROOT%"=="" set ROOT=..\..\Katlas_Sources_v0.2.2_Outputs
call run_setup.cmd || exit /b 1
call run_selftest.cmd || exit /b 1
python -m sst_katlas_conditioning.cli focus "%ROOT%\links\02\L2a1\katlas.json" "outputs\focus_L2a1\links\02\L2a1" --config config\basic.json || exit /b 1
