@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (echo ERROR: Run run_00_setup.cmd first. & popd & exit /b 1)
"%PY%" -m unittest discover -s tests -v || exit /b 1
popd
endlocal
