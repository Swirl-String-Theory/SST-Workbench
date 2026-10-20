@echo off
setlocal
cd /d "%~dp0"
python -m unittest discover -s tests -v || exit /b 1
python -m experiment.standalone || exit /b 1
endlocal
