@echo off
setlocal
cd /d "%~dp0"
python setup.py build_ext --inplace
endlocal
