@echo off
setlocal EnableExtensions
pushd "%~dp0"
where python >nul 2>nul || (echo FAIL: Python missing. & popd & exit /b 2)
python legacy_v020\validate_integrated.py
if errorlevel 1 (echo FAIL legacy-v020 & popd & exit /b 1)
python tests\validate_v030.py
if errorlevel 1 (echo FAIL v030 & popd & exit /b 1)
python src\generate_figures.py
if errorlevel 1 (echo FAIL figures & popd & exit /b 1)
if /I "%~1"=="PDF" (
  where pdflatex >nul 2>nul
  if errorlevel 1 (echo NOTE: no local pdflatex; use bundled PDF.) else (
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory=results SST_VAM5_SST17_PKLSA_Resonance_v0.3.0.tex
    if errorlevel 1 (echo FAIL PDF & popd & exit /b 3)
    pdflatex -interaction=nonstopmode -halt-on-error -output-directory=results SST_VAM5_SST17_PKLSA_Resonance_v0.3.0.tex >nul
    copy /Y results\SST_VAM5_SST17_PKLSA_Resonance_v0.3.0.pdf SST_VAM5_SST17_PKLSA_Resonance_v0.3.0.pdf >nul
  )
)
if /I "%~1"=="NATIVE" (echo BLOCKED: source-native PKLSA engine not bundled; G5/G6 not executed. & popd & exit /b 4)
echo DEVELOPMENT COMPLETE: tests of surrogate, synthetic spectra, and thermodynamics only. PKLSA G5/G6 NOT RUN.
popd
exit /b 0
