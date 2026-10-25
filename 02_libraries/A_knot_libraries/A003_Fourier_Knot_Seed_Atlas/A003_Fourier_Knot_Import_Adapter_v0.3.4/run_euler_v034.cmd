@echo off
setlocal EnableExtensions
set "ADAPTER_ROOT=%~dp0"
set "WORKBENCH=C:\workspace\projects\SST-Workbench"
if defined SST_WORKBENCH_ROOT set "WORKBENCH=%SST_WORKBENCH_ROOT%"
set "C005_ROOT=%WORKBENCH%\01_research\C_dynamics\C005_fermat_biot_savart\C005-v0.6.1"
if defined SST_C005_ROOT set "C005_ROOT=%SST_C005_ROOT%"
set "EULER_OUT=%ADAPTER_ROOT%..\A003_Fourier_Knot_Import_Adapter_v0.3.4-outputs\euler_%RANDOM%_%RANDOM%"
python "%ADAPTER_ROOT%euler_3d_qualification_v034.py" --out "%EULER_OUT%" %*
exit /b %ERRORLEVEL%
