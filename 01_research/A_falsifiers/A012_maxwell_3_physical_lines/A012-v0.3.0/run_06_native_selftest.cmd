@echo off
setlocal EnableExtensions
call "%~dp0_env.cmd"
if errorlevel 1 exit /b %errorlevel%
"%PY%" -m sst_maxwell3_blind.cli selftest --native --threads %SST_NATIVE_THREADS%
exit /b %errorlevel%
