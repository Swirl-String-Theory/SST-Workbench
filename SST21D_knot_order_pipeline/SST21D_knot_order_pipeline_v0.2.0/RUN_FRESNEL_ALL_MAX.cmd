@echo off
setlocal
cd /d "%~dp0"
call RUN_BUILD_NATIVE.bat
if errorlevel 1 exit /b %errorlevel%
py -3 -m sst21d fresnel-scan --input data\Fresnel_FourierSeries.zip --origin-overrides data\fseries_origin_overrides.csv --out outputs\fresnel_scan_max
if errorlevel 1 exit /b %errorlevel%
py -3 -m sst21d fresnel-static --input data\Fresnel_FourierSeries.zip --samples 1200 --prefer short --metadata data\sst21_metadata_seed.csv --origin-overrides data\fseries_origin_overrides.csv --out outputs\fresnel_static_max --require-native
if errorlevel 1 exit /b %errorlevel%
py -3 -m sst21d fresnel-convergence --input data\Fresnel_FourierSeries.zip --representation fseries --resolutions 128 256 512 1024 --origin-overrides data\fseries_origin_overrides.csv --out outputs\fresnel_convergence_fseries --require-native
if errorlevel 1 exit /b %errorlevel%
py -3 -m sst21d fresnel-convergence --input data\Fresnel_FourierSeries.zip --representation short --resolutions 128 256 512 1024 --origin-overrides data\fseries_origin_overrides.csv --out outputs\fresnel_convergence_short --require-native
if errorlevel 1 exit /b %errorlevel%
py -3 -m sst21d fresnel-export --input data\Fresnel_FourierSeries.zip --samples 800 --representation short --format both --origin-overrides data\fseries_origin_overrides.csv --out exports\fresnel_ridgerunner_max
if errorlevel 1 exit /b %errorlevel%
echo.
echo MAX COMPLETE
