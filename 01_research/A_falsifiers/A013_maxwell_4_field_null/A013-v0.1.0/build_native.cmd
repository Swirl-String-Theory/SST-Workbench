@echo off
setlocal
cmake -S native -B native\build
if errorlevel 1 exit /b %errorlevel%
cmake --build native\build --config Release
