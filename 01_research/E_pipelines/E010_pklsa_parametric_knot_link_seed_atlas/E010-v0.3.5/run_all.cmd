@echo off
setlocal
cd /d "%~dp0"
python -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
python build_ruban_family.py --dry-run
if errorlevel 1 exit /b 1
python build_ruban_family.py --mode pilot --archive %*
exit /b %errorlevel%
