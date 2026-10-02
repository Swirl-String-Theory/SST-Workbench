@echo off
setlocal
cd /d "%~dp0"
echo [finite-core-spectral] Python: %CD%
python -c "import sys; print('[finite-core-spectral] Python executable:', sys.executable)"
python -m pip install -r requirements.txt
exit /b %ERRORLEVEL%
