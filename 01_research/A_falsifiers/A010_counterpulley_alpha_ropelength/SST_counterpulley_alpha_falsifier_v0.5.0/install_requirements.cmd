@echo off
setlocal
python -m pip install -U pip
python -m pip install -r requirements.txt
if errorlevel 1 exit /b %errorlevel%
echo [SST] requirements installed.
