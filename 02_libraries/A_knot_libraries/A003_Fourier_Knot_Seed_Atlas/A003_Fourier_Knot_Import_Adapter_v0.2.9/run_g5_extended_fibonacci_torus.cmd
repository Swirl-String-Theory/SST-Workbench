@echo off
setlocal EnableExtensions
set "HERE=%~dp0"
set "ATLAS=%HERE%..\A003-v0.1.2"
if defined SST_ATLAS_ROOT set "ATLAS=%SST_ATLAS_ROOT%"
if not exist "%ATLAS%\manifest.json" (
 echo FAIL_CLOSED: missing A003-v0.1.2 atlas 1>&2
 exit /b 2
)
rem G5 extended runs symbolic pyknotid only on bounded small knot cases.
rem High-crossing torus knots are explicitly UNRESOLVED, never certified.
python "%HERE%fourier_atlas_adapter.py" --atlas "%ATLAS%" --out "%HERE%outputs_g5_extended_fibonacci_torus" --reference-core-radius-units 0.05 --g5 --g5-extended --g5-family fibonacci_torus --g5-resolutions BASIC --g5-extended-max-crossings 12 --require-g5-evidence catalog
exit /b %errorlevel%
