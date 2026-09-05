@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install -e . --no-build-isolation
if errorlevel 1 goto :error
py -3 -m sstcbhf convergence --database data\ideal_favorites.txt --id 3:1:1 --resolutions 128 192 256 384 --out outputs\gilbert_3_1_convergence
set RC=%ERRORLEVEL%
pause
exit /b %RC%
:error
echo Installation failed.
pause
exit /b 1
