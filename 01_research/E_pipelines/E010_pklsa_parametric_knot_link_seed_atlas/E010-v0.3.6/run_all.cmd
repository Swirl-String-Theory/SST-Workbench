@echo off
setlocal
cd /d "%~dp0"
python -m pip install -r requirements.txt || exit /b 1
python -m unittest discover -s tests -v || exit /b 1
python build_ruban_family.py --mode fine --archive || exit /b 1
endlocal
