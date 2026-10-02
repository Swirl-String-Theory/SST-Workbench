@echo off
setlocal
cd /d "%~dp0"
if not exist "data\ideal_favorites.txt" (
  echo Missing data\ideal_favorites.txt
  pause
  exit /b 2
)
py -3 -m sst21d convergence --database data\ideal_favorites.txt --resolutions 128 256 512 --out outputs\convergence_favorites --require-native
if errorlevel 1 exit /b %errorlevel%
echo Wrote outputs\convergence_favorites\convergence_summary.csv
pause
