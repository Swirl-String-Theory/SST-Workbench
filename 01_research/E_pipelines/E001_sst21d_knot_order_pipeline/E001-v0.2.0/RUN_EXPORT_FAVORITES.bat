@echo off
setlocal
cd /d "%~dp0"
if not exist "data\ideal_favorites.txt" exit /b 2
py -3 -m sst21d export --database data\ideal_favorites.txt --ids 0:1:1 3:1:1 4:1:1 5:1:2 --samples 300 --format both --out exports\favorites
pause
