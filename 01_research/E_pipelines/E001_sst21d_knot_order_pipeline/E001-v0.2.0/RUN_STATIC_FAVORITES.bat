@echo off
setlocal
cd /d "%~dp0"
if not exist "data\ideal_favorites.txt" (
  echo Missing data\ideal_favorites.txt
  echo Copy your Brian Gilbert database into the data folder first.
  pause
  exit /b 2
)
py -3 -m sst21d static --database data\ideal_favorites.txt --samples 600 --metadata data\sst21_metadata_seed.csv --out outputs\static_favorites --require-native
if errorlevel 1 exit /b %errorlevel%
echo Wrote outputs\static_favorites\sst21d_master.csv
pause
