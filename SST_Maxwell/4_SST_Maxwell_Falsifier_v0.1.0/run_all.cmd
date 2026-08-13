@echo off
setlocal
python -m maxwell_sst.cli demo --out outputs_demo
exit /b %ERRORLEVEL%
