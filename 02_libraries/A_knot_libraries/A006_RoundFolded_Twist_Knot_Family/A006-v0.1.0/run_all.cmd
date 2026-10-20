@echo off
setlocal
cd /d "%~dp0"
set MODE=%~1
if "%MODE%"=="" set MODE=ALL
py -3 -c "import numpy,scipy" || (echo [FAIL] Python NumPy/SciPy missing & exit /b 1)
if /I "%MODE%"=="ACQUIRE" (
    py -3 src\build.py --mode ACQUIRE || exit /b 1
    echo Open acquisition\acquire_Tm7.kpc within KnotPlot; no KnotPlot runtime invoked by this CMD.
    exit /b 0
)
if /I "%MODE%"=="BASIC" (
    py -3 src\build.py --mode ALL --n 256 || exit /b 1
) else if /I "%MODE%"=="FULL" (
    py -3 src\build.py --mode ALL --n 512 || exit /b 1
) else if /I "%MODE%"=="BORROMEAN" (
    py -3 src\build.py --mode BORROMEAN --n 256 || exit /b 1
) else (
    py -3 src\build.py --mode ALL --n 256 || exit /b 1
)
py -3 -m unittest discover -s tests -v || exit /b 1
echo [PASS] Generated static geometric candidates. KnotPlot runtime and topology NOT CERTIFIED.
