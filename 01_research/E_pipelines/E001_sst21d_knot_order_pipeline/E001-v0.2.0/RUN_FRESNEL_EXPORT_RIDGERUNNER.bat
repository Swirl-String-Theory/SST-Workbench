@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install -e . --no-build-isolation
if errorlevel 1 exit /b %errorlevel%
py -3 -m sst21d fresnel-export --input data\Fresnel_FourierSeries.zip --samples 400 --representation short --format both --origin-overrides data\fseries_origin_overrides.csv --out exports\fresnel_ridgerunner
