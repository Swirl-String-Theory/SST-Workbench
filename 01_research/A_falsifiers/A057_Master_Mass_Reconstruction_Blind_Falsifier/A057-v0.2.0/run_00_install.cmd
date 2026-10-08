@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
python -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
pushd native_ext
if exist build rmdir /s /q build
for %%F in (mm_native*.pyd mm_native*.so) do if exist "%%F" del /q "%%F"
python setup.py build_ext --inplace --force
if errorlevel 1 (popd & exit /b 1)
popd
python -m pytest tests -q
if errorlevel 1 exit /b 1
python -m master_mass.commitment --verify
if errorlevel 1 exit /b 1
exit /b 0
