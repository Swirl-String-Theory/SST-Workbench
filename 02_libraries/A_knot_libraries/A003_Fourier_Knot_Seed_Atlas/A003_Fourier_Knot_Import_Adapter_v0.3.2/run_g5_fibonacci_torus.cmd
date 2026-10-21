@echo off
setlocal EnableExtensions
set "HERE=%~dp0"
set "SST_ATLAS_ROOT=%HERE%..\A003-v0.1.2"
if not exist "%SST_ATLAS_ROOT%\manifest.json" (
 echo FAIL_CLOSED: A003-v0.1.2 atlas missing 1>&2
 exit /b 2
)
python "%HERE%fourier_atlas_adapter.py" --atlas "%SST_ATLAS_ROOT%" --out "%HERE%outputs_g5_fibonacci_torus" --reference-core-radius-units 0.05 --g5 --g5-family fibonacci_torus --g5-resolutions BASIC --require-g5-evidence catalog
exit /b %errorlevel%
