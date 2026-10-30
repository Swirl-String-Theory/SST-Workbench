
@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo A075-v0.2.9 - RUBAN DEPOSITION MATRIX
echo ==========================================

echo [1/7] BOX L=5, N=200
call run_all.cmd RUBAN_DEPOSITION --deposition-grids 200 --deposition-sigmas 0.075 --deposition-boxes 5 --allow-expensive --threads 12
if errorlevel 1 goto failed

echo [2/7] BOX L=6, N=240
call run_all.cmd RUBAN_DEPOSITION --deposition-grids 240 --deposition-sigmas 0.075 --deposition-boxes 6 --allow-expensive --threads 12
if errorlevel 1 goto failed

echo [3/7] SPATIAL N=256
call run_all.cmd RUBAN_DEPOSITION --deposition-grids 256 --deposition-sigmas 0.075 --deposition-boxes 4 --allow-expensive --threads 12
if errorlevel 1 goto failed

echo [4/7] CORE SIGMA=0.065
call run_all.cmd RUBAN_DEPOSITION --deposition-grids 192,224,256 --deposition-sigmas 0.065 --deposition-boxes 4 --allow-expensive --threads 12
if errorlevel 1 goto failed

echo [5/7] CORE SIGMA=0.055
call run_all.cmd RUBAN_DEPOSITION --deposition-grids 224,256 --deposition-sigmas 0.055 --deposition-boxes 4 --allow-expensive --threads 12
if errorlevel 1 goto failed

echo [6/7] CORE SIGMA=0.070
call run_all.cmd RUBAN_DEPOSITION --deposition-grids 192,224,256 --deposition-sigmas 0.070 --deposition-boxes 4 --allow-expensive --threads 12
if errorlevel 1 goto failed

echo [7/7] BOX L=5, N=240, SIGMA=0.065
call run_all.cmd RUBAN_DEPOSITION --deposition-grids 240 --deposition-sigmas 0.065 --deposition-boxes 5 --allow-expensive --threads 12
if errorlevel 1 goto failed

echo ==========================================
echo ALL DEPOSITION TESTS COMPLETED
echo ==========================================
pause
exit /b 0

:failed
echo ==========================================
echo TEST FAILED - MATRIX STOPPED
echo ==========================================
pause
exit /b 1
