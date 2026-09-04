@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install -e . --no-build-isolation
if errorlevel 1 exit /b %errorlevel%
py -3 -m sst21d build-native
if errorlevel 1 exit /b %errorlevel%
py -3 -m sst21d fresnel-static --input data\Fresnel_FourierSeries.zip --samples 600 --prefer short --metadata data\sst21_metadata_seed.csv --origin-overrides data\fseries_origin_overrides.csv --out outputs\fresnel_static --require-native
