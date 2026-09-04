@echo off
setlocal
cd /d "%~dp0"
set PYTHONPATH=%CD%\src;%CD%
.venv\Scripts\python.exe -m sst_phase_delay_falsifier.cli evaluate --pred results\delay_predictions.json --measure results\nonlinear_measurements.json --out results\BLIND_EVALUATION.json
set RC=%ERRORLEVEL%
certutil -hashfile results\delay_predictions.json SHA256 > results\delay_predictions.sha256.txt
certutil -hashfile results\nonlinear_measurements.json SHA256 > results\nonlinear_measurements.sha256.txt
certutil -hashfile results\BLIND_EVALUATION.json SHA256 > results\BLIND_EVALUATION.sha256.txt
exit /b %RC%
