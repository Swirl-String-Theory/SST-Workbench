@echo off
setlocal
call .venv\Scripts\activate.bat || exit /b 1
python -m unittest discover -s tests -v || exit /b 1
endlocal
