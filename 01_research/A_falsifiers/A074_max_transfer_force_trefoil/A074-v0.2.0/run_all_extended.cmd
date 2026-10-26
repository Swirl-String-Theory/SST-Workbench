@echo off
setlocal
cd /d "%~dp0"
call run_tests.cmd || exit /b %errorlevel%
call run_equilibrium_search.cmd || exit /b %errorlevel%
call run_euler.cmd --extended || exit /b %errorlevel%
echo Full Euler campaign completed; this does NOT imply framework FULL/CERTIFY.
