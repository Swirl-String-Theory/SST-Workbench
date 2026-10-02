@echo off
setlocal
set PYTHONPATH=%~dp0src
python -m pytest -q "%~dp0tests"
endlocal
