@echo off
setlocal
cd /d "%~dp0"
python setup.py build_ext --inplace || exit /b 1
python -c "import vortex_shear_native; print('native import OK:', vortex_shear_native.__doc__)" || exit /b 1
endlocal
