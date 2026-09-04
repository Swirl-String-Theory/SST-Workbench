@echo off
setlocal
cd /d "%~dp0"
echo [finite-core-spectral] package: v0.1.2.4
python -m finite_core_spectral.native_runtime --strict
exit /b %ERRORLEVEL%
