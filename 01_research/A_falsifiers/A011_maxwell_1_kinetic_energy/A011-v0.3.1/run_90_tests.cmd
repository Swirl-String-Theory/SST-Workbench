@echo off
setlocal
call "%~dp0_common.cmd" || exit /b 1
pushd "%~dp0"
"%PYTHON_EXE%" -m pytest -q
set ERR=%errorlevel%
popd
exit /b %ERR%
