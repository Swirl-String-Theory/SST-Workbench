@echo off
setlocal
cd /d "%~dp0"
python -m finite_core_spectral.build_ext_if_needed --force --strict
exit /b %ERRORLEVEL%
