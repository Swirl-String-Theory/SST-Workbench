@echo off
setlocal
pushd "%~dp0tools\VCCR_v0.2.0" || exit /b 1
call run_vccr.cmd %*
set "CODE=%errorlevel%"
popd
exit /b %CODE%
