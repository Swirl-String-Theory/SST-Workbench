@echo off
setlocal EnableExtensions
set "HERE=%~dp0"
set "ATLAS=%HERE%..\A003-v0.1.2"
if defined SST_ATLAS_ROOT set "ATLAS=%SST_ATLAS_ROOT%"
if not exist "%ATLAS%\manifest.json" (
 echo FAIL_CLOSED: missing A003-v0.1.2 atlas 1>&2
 exit /b 2
)
rem Frozen v0.2.4 primary projections; v0.2.5 extra projections are diagnosis only.
rem Expected exit 2 when a primary projection still disagrees: keep FAIL_CLOSED.
python "%HERE%fourier_atlas_adapter.py" --atlas "%ATLAS%" --out "%HERE%outputs_g5_projection_robustness" --reference-core-radius-units 0.05 --g5 --g5-extended --g5-family fibonacci_torus --g5-resolutions BASIC --g5-extended-max-crossings 12 --require-g5-evidence catalog
exit /b %errorlevel%
