@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~1"=="" echo Usage: run_spectral_extension_baseline_check.cmd ^<v0.4.7_output_dir_or_zip^> & exit /b 2
if not exist ".venv\Scripts\python.exe" call run_install.cmd || exit /b 1
if not exist "outputs_spectral_baseline_check" mkdir "outputs_spectral_baseline_check"
".venv\Scripts\python.exe" run_spectral_extension.py --out-dir "outputs_spectral_baseline_check" --backend cpu --baseline "%~1" --baseline-check-only
exit /b %errorlevel%
