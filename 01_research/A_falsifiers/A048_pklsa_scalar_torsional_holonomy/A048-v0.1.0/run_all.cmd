@echo off
setlocal
cd /d "%~dp0"
echo [1/10] Prepare blind cases
python prepare_blind.py || exit /b 1
echo [2/10] Record environment
python record_environment.py || exit /b 1
echo [3/10] Python blind campaign
python run_blind.py || exit /b 1
echo [4/10] Python tests
python -m pytest -q tests -k "not native" || exit /b 1
echo [5/10] Build C++17/pybind11 backend
call build_native.cmd || exit /b 1
echo [6/10] Record native module and run native blind campaign
python record_native.py || exit /b 1
python run_native_blind.py || exit /b 1
echo [7/10] Native/parity qualification
python run_backend_parity.py || exit /b 1
python -m pytest -q tests || exit /b 1
echo [8/10] Seal blind evidence
python seal_blind.py || exit /b 1
echo [9/10] Reveal
python reveal.py || exit /b 1
echo [10/10] Package
python package_outputs.py || exit /b 1
echo DONE
