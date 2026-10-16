@echo off
setlocal
cd /d "%~dp0"
py -3 audit_native_census_v012.py --census-dir "Build_Knot_Link_Torus_KnotPlot_Scripts/falsifier_census_v0.1.2" --out "audited_v0.1.2_data"
exit /b %ERRORLEVEL%
