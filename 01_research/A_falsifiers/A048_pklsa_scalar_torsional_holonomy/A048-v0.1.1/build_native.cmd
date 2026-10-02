@echo off
setlocal
cd /d "%~dp0"
python setup.py build_ext --inplace
if errorlevel 1 exit /b %errorlevel%
python -c "import torsion_native; print('torsion_native import OK')"
