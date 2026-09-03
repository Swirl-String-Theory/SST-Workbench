@echo off
setlocal
call .venv\Scripts\activate.bat || exit /b 1
if exist build\temp_native rmdir /s /q build\temp_native
python setup_native.py build_ext --inplace --build-temp build\temp_native || exit /b 1
python -c "from sst_wp.native_ext import NATIVE_AVAILABLE; assert NATIVE_AVAILABLE; print('native backend loaded')" || exit /b 1
endlocal
