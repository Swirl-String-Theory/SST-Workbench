@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=%CD%\src;%CD%"
.venv\Scripts\python.exe -m sst_phase_delay_falsifier.cli evaluate --pred results\packet_delay_predictions.json --measure results\nonlinear_measurements.json --manifest blind_work\sealed_manifest.json --audit blind_work\dataset_audit.json --out results\BLIND_EVALUATION.json
set RC=%ERRORLEVEL%
certutil -hashfile results\packet_delay_predictions.json SHA256 > results\packet_delay_predictions.sha256.txt
certutil -hashfile results\nonlinear_measurements.json SHA256 > results\nonlinear_measurements.sha256.txt
certutil -hashfile results\BLIND_EVALUATION.json SHA256 > results\BLIND_EVALUATION.sha256.txt
exit /b %RC%
