@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo [SST VAM-5 Repair] Algebraic regression (not a physical Euler simulation)
set "PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
"%PYTHON%" validate_repair.py
if errorlevel 1 (
    echo FAIL: algebraic regression failed.
    exit /b 1
)
where latexmk >nul 2>nul
if not errorlevel 1 (
    echo [SST VAM-5 Repair] Compiling source PDF
    latexmk -pdf -interaction=nonstopmode -halt-on-error SST_VAM5_Lagrangian_Repair_v0.1.0.tex
    if errorlevel 1 exit /b 1
) else (
    echo [SST VAM-5 Repair] latexmk not found, keeping bundled PDF.
)
echo PASS: local analytical checks completed. Dynamic qualification remains unresolved.
exit /b 0
