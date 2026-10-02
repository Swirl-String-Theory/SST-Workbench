@echo off
setlocal
cd /d "%~dp0"
set SST_BACKEND=python
python prepare_blind.py || exit /b 1
python run_blind.py || exit /b 1
python -m pytest -q || exit /b 1
python seal_blind.py || exit /b 1
python reveal.py || exit /b 1
endlocal
