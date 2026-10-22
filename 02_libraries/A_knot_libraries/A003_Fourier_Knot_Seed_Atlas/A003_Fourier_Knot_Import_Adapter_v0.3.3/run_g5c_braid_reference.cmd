@echo off
setlocal EnableExtensions
set "HERE=%~dp0"
set "ATLAS=%HERE%..\A003-v0.1.2"
if defined SST_ATLAS_ROOT set "ATLAS=%SST_ATLAS_ROOT%"
python "%HERE%g5c_braid_reference.py" --atlas "%ATLAS%" --out "%HERE%outputs_g5c_braid_reference"
exit /b %errorlevel%
