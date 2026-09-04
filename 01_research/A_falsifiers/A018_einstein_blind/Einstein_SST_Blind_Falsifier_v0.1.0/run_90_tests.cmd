@echo off
setlocal EnableExtensions
pushd "%~dp0"
call "%~dp0_common.cmd" || goto :fail
"%PYTHON_EXE%" -m unittest tests.test_reference -v || goto :fail
"%PYTHON_EXE%" run_native_selfcheck.py || goto :fail
popd
exit /b 0
:fail
popd
exit /b 1
