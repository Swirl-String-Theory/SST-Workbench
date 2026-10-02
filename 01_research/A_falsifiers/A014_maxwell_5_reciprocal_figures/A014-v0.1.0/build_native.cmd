@echo off
setlocal
cd /d "%~dp0"
if not exist build mkdir build
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release || exit /b 1
cmake --build build --config Release --parallel || exit /b 1
echo Native core built.
