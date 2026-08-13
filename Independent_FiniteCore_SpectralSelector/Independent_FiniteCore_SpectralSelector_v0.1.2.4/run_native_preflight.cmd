@echo off
setlocal
cd /d "%~dp0"
echo [finite-core-spectral] package: v0.1.2.4
echo [finite-core-spectral] python: %CD%
python -m finite_core_spectral.build_ext_if_needed --force --strict
if errorlevel 1 exit /b %ERRORLEVEL%
python -m finite_core_spectral.native_runtime --strict
exit /b %ERRORLEVEL%
