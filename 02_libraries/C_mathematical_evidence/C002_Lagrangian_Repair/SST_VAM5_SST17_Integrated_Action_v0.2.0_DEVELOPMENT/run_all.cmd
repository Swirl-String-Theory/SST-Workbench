@echo off
setlocal EnableExtensions
pushd "%~dp0"
set "PYTHON_BIN=python"
where python >nul 2>nul || (echo ERROR: Python not found on PATH. & popd & exit /b 2)
"%PYTHON_BIN%" tests\validate_integrated.py
if errorlevel 1 (echo FAIL: regression tests failed. & popd & exit /b 1)
if /I "%~1"=="PDF" (
  where latexmk >nul 2>nul
  if errorlevel 1 (
    echo NOTE: latexmk not installed, using precompiled PDF.
  ) else (
    latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=results SST_VAM5_SST17_Integrated_Action_v0.2.0.tex
    if errorlevel 1 (echo ERROR: PDF compile failed. & popd & exit /b 3)
    copy /Y "results\SST_VAM5_SST17_Integrated_Action_v0.2.0.pdf" "SST_VAM5_SST17_Integrated_Action_v0.2.0.pdf" >nul
  )
)
echo COMPLETE: algebraic and frozen-wave regression only; no PKLSA or 3D coupled model certified.
popd
exit /b 0
