@echo off
setlocal
cd /d "%~dp0"
python -m pip install -r requirements.txt || exit /b 1
python -m pip install -e . --no-build-isolation || exit /b 1
endlocal
