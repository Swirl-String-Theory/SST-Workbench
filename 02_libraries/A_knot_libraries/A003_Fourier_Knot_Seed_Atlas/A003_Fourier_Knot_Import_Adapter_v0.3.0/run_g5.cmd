@echo off
setlocal EnableExtensions
set "ADAPTER_ROOT=%~dp0"
set "ATLAS_ROOT=%ADAPTER_ROOT%..\A003-v0.1.2"
if defined SST_ATLAS_ROOT set "ATLAS_ROOT=%SST_ATLAS_ROOT%"
if not "%~1"=="" set "ATLAS_ROOT=%~1"
if not exist "%ATLAS_ROOT%\manifest.json" (
  echo FAIL_CLOSED: Atlas ontbreekt: "%ATLAS_ROOT%\manifest.json" 1>&2
  exit /b 2
)
set "A_STAR=0.05"
if defined SST_A003_REFERENCE_CORE_RADIUS_UNITS set "A_STAR=%SST_A003_REFERENCE_CORE_RADIUS_UNITS%"
if defined SST_A003_A_STAR set "A_STAR=%SST_A003_A_STAR%"
if not "%~2"=="" set "A_STAR=%~2"
rem Optional external provider: python -m pip install pyknotid
rem BASIC = 1200 and 2400 points for all 48 analytic seeds; potentially expensive.
python "%ADAPTER_ROOT%fourier_atlas_adapter.py" --atlas "%ATLAS_ROOT%" --out "%ADAPTER_ROOT%outputs" --reference-core-radius-units "%A_STAR%" --g5 --g5-sampling uniform_t --g5-resolutions BASIC --require-g5-evidence catalog
exit /b %errorlevel%
