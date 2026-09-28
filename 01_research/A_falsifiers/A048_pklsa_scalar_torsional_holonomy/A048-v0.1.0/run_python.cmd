@echo off
setlocal
cd /d "%~dp0"
echo [1/7] Prepare blind cases
python prepare_blind.py || exit /b 1
echo [2/7] Record environment
python record_environment.py || exit /b 1
echo [3/7] Python blind campaign
python run_blind.py || exit /b 1
echo [4/7] Python tests
python -m pytest -q tests || exit /b 1
echo [5/7] Seal blind evidence
python seal_blind.py || exit /b 1
echo [6/7] Reveal
python reveal.py || exit /b 1
echo [7/7] Package
python package_outputs.py || exit /b 1
echo DONE
