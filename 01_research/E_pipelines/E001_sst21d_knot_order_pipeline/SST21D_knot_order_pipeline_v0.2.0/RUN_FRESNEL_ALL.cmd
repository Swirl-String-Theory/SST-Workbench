@echo off
setlocal
cd /d "%~dp0"
call RUN_BUILD_NATIVE.bat
if errorlevel 1 exit /b %errorlevel%
py -3 -m sst21d fresnel-scan --input data\Fresnel_FourierSeries.zip --origin-overrides data\fseries_origin_overrides.csv --out outputs\fresnel_scan
if errorlevel 1 exit /b %errorlevel%
py -3 -m sst21d fresnel-static --input data\Fresnel_FourierSeries.zip --samples 600 --prefer short --metadata data\sst21_metadata_seed.csv --origin-overrides data\fseries_origin_overrides.csv --out outputs\fresnel_static --require-native
if errorlevel 1 exit /b %errorlevel%
py -3 -m sst21d fresnel-export --input data\Fresnel_FourierSeries.zip --samples 400 --representation short --format both --origin-overrides data\fseries_origin_overrides.csv --out exports\fresnel_ridgerunner
if errorlevel 1 exit /b %errorlevel%
echo.
echo COMPLETE: outputs\fresnel_static and exports\fresnel_ridgerunner
