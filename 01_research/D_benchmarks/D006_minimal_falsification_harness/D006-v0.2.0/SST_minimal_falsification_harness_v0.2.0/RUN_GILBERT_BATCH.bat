@echo off
setlocal
cd /d "%~dp0"

python sst_minimal_falsification.py gilbert-batch ^
  --database data\ideal_favorites.txt ^
  --samples 600 ^
  --length-source reported ^
  --core-profile unit ^
  --out gilbert_feature_batch.json ^
  --csv-out gilbert_feature_batch.csv
if errorlevel 1 goto :error

echo.
echo Cross-knot feature batch completed.
echo Output: gilbert_feature_batch.json
echo Output: gilbert_feature_batch.csv
pause
exit /b 0

:error
echo.
echo ERROR: Gilbert batch extraction failed.
pause
exit /b 1
