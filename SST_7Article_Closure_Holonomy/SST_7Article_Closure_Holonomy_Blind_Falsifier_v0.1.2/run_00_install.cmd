@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [SST7] Creating virtual environment...
  py -3 -m venv .venv || goto :fail
)
call ".venv\Scripts\activate.bat" || goto :fail
python -m pip install --upgrade pip setuptools wheel || goto :fail
python -m pip install -r requirements.txt || goto :fail
set SST_NATIVE_OPENMP=1
python -m native_ext.build_ext_if_needed || goto :fail
python scripts\selftest.py || goto :fail
python scripts\selftest_blind.py || goto :fail
echo [SST7] Environment ready.
exit /b 0
:fail
echo [SST7] INSTALL/SELFTEST FAILED
exit /b 1
