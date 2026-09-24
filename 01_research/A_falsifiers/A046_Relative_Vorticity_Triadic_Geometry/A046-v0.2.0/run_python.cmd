@echo off
setlocal
cd /d "%~dp0"
set "OUT=..\A046_Relative_Vorticity_Triadic_Geometry_Falsifier_v0.2.0-outputs\BLIND"
set SST_BACKEND=python

echo [1/6] Prepare blind evidence tree
python prepare_blind.py || exit /b 1

echo [2/6] Python reference campaign
python tools\run_logged.py --log "%OUT%\logs\python_campaign.log" -- python run_blind.py || exit /b 1

echo [3/6] Python tests
python tools\run_logged.py --log "%OUT%\logs\python_tests.log" -- python -m pytest -q || exit /b 1
python record_environment.py --mode python || exit /b 1

echo [4/6] Seal blind evidence
python seal_blind.py || exit /b 1

echo [5/6] Reveal
python reveal.py || exit /b 1

echo [6/6] Package outputs
python package_outputs.py || exit /b 1

endlocal
