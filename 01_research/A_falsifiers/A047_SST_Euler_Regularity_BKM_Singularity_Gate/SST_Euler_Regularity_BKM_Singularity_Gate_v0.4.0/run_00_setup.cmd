@echo off
setlocal
cd /d "%~dp0"
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat || exit /b 1
python -m pip install --upgrade pip setuptools wheel pybind11 numpy pytest || exit /b 1
python -m pip install -e . || exit /b 1
python -m pytest -q || exit /b 1
echo A047 v0.4.0 setup/tests complete.
