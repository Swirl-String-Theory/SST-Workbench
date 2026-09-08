@echo off
setlocal
cd /d "%~dp0"

python sst_minimal_falsification.py gilbert-list ^
  --database data\ideal_favorites.txt ^
  --out gilbert_manifest.json
if errorlevel 1 goto :error

python sst_minimal_falsification.py gilbert-geometry ^
  --database data\ideal_favorites.txt ^
  --id 3:1:1 ^
  --samples 1200 ^
  --length-source reported ^
  --core-profile unit ^
  --out gilbert_trefoil_features.json
if errorlevel 1 goto :error

echo.
echo Trefoil extraction completed.
pause
exit /b 0

:error
echo.
echo ERROR: Gilbert trefoil extraction failed.
pause
exit /b 1
