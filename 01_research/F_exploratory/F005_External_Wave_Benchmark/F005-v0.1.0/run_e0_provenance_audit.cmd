@echo off
setlocal
cd /d "%~dp0"
py -3 data\f005_e0_provenance_audit.py --root . --geometry config\EULER_GEOMETRY_REQUIRED.json --output outputs\f005_e0_provenance_audit_v0.5.0_p1
exit /b %ERRORLEVEL%
