@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHONPATH=%ROOT%;%PYTHONPATH%"
python -m resolver.studies %*
exit /b %errorlevel%
