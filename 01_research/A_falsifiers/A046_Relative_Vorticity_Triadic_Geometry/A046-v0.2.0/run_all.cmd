@echo off
setlocal
cd /d "%~dp0"
set "OUT=..\A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs\BLIND"

echo [1/8] Prepare blind evidence tree
python prepare_blind.py || exit /b 1

echo [2/8] Python reference campaign
set SST_BACKEND=python
python tools\run_logged.py --log "%OUT%\logs\python_campaign.log" -- python run_blind.py || exit /b 1

echo [3/8] Python tests and runtime evidence
python tools\run_logged.py --log "%OUT%\logs\python_tests.log" -- python -m pytest -q || exit /b 1
python record_environment.py --mode python || exit /b 1

echo [4/8] Build native extension
python tools\run_logged.py --log "%OUT%\logs\native_build.log" -- cmd /c build_native.cmd || exit /b 1

echo [5/8] Native campaign, tests, and parity
set SST_BACKEND=native
python tools\run_logged.py --log "%OUT%\logs\native_campaign.log" -- python run_native_blind.py || exit /b 1
python tools\run_logged.py --log "%OUT%\logs\native_tests.log" -- python -m pytest -q || exit /b 1
python record_environment.py --mode native || exit /b 1
python tools\run_logged.py --log "%OUT%\logs\backend_parity.log" -- python run_backend_parity.py || exit /b 1

echo [6/8] Seal complete blind evidence
python seal_blind.py || exit /b 1

echo [7/8] Reveal
python reveal.py || exit /b 1

echo [8/8] Package outputs
python package_outputs.py || exit /b 1

endlocal
