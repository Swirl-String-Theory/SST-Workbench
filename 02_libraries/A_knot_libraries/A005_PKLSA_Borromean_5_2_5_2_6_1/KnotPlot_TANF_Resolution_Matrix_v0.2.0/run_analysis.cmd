@echo off
cd /d "%~dp0"
py -3 tools\analyze_matrix.py --tier %1
if errorlevel 1 echo NOTE: This report is partial or has flagged issues.
