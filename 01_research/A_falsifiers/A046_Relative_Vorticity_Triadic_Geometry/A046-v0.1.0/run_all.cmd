@echo off
setlocal
cd /d "%~dp0"

echo [1/6] Python reference campaign
set SST_BACKEND=python
python prepare_blind.py || exit /b 1
python run_blind.py || exit /b 1

echo [2/6] Python tests
python -m pytest -q || exit /b 1

echo [3/6] Build native extension
call build_native.cmd || exit /b 1

echo [4/6] Native-aware tests
set SST_BACKEND=native
python -m pytest -q || exit /b 1

echo [5/6] Seal blind result
python seal_blind.py || exit /b 1

echo [6/6] Reveal
python reveal.py || exit /b 1

endlocal
