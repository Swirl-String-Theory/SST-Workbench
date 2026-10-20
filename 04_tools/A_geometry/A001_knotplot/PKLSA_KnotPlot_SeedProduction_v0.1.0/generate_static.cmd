@echo off
setlocal
set "ROOT=%~dp0"
python -m unittest discover -s "%ROOT%tests" -v || exit /b 1
python "%ROOT%src\seedproduction.py" --out "%ROOT%production_out" || exit /b 1
@echo STATIC GEOMETRY BUILT. No KnotPlot/Euler dynamics executed.
exit /b 0
