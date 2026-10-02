@echo off
rem Central paths. Edit only this file if the SST workspace moves.
set "SST_WORKBENCH_ROOT=C:\workspace\projects\SST-Workbench"
set "SST_KNOT_DIR=C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
set "SST_SHARED_VENV=C:\workspace\projects\SST-Workbench\.venv"
if not defined SST_NATIVE_THREADS set "SST_NATIVE_THREADS=16"
