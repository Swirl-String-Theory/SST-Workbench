@echo off
setlocal
cd /d "%~dp0"
.venv\Scripts\python.exe -m a055_spectrum.cli selftest --require-native
