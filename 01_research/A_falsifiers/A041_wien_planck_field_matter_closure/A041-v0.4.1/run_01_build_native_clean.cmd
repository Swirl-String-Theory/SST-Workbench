@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
rem Launch a child command processor with /d so HKCU/HKLM Command Processor AutoRun is ignored.
"%ComSpec%" /d /s /c ""%~dp0run_01_build_native.cmd""
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%
