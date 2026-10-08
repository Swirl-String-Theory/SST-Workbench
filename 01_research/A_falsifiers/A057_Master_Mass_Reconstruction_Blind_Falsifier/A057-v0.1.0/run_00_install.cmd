@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
pushd native_ext
python setup.py build_ext --inplace
if errorlevel 1 (popd & exit /b 1)
popd
python -m pytest tests -q
exit /b %ERRORLEVEL%
