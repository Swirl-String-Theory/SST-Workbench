@echo off
setlocal
python make_synthetic_controls.py || exit /b 1
python tests\test_controls.py || exit /b 1
echo All Maxwell-SST DFC tests passed.
