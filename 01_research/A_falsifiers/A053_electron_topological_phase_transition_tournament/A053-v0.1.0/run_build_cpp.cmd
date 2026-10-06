@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "VENV=%CD%\.venv"
set "PY=%VENV%\Scripts\python.exe"
set "CMAKE=%VENV%\Scripts\cmake.exe"
set "NINJA=%VENV%\Scripts\ninja.exe"

if not exist "%PY%" (
    echo [A053] Creating local Python virtual environment...
    where py >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python launcher ^(py.exe^) was not found on PATH.
        exit /b 10
    )
    py -3 -m venv "%VENV%"
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv.
        exit /b 11
    )
)

echo [A053] Installing/updating native build dependencies...
"%PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 12
"%PY%" -m pip install --upgrade pybind11 cmake ninja
if errorlevel 1 (
    echo [ERROR] Failed to install pybind11/cmake/ninja into .venv.
    exit /b 13
)

set "PYBIND11_CMAKE_DIR="
for /f "usebackq delims=" %%I in (`"%PY%" -m pybind11 --cmakedir`) do set "PYBIND11_CMAKE_DIR=%%I"

if not defined PYBIND11_CMAKE_DIR (
    echo [ERROR] python -m pybind11 --cmakedir returned no directory.
    "%PY%" -m pip show pybind11
    exit /b 14
)

if not exist "%PYBIND11_CMAKE_DIR%\pybind11Config.cmake" (
    echo [ERROR] pybind11Config.cmake was not found at:
    echo         %PYBIND11_CMAKE_DIR%
    "%PY%" -m pip show pybind11
    exit /b 15
)

if not exist "%CMAKE%" (
    echo [ERROR] venv CMake executable not found: %CMAKE%
    exit /b 16
)
if not exist "%NINJA%" (
    echo [ERROR] venv Ninja executable not found: %NINJA%
    exit /b 17
)

echo [A053] Python:   %PY%
"%PY%" --version
echo [A053] pybind11: %PYBIND11_CMAKE_DIR%
"%PY%" -c "import pybind11; print('[A053] pybind11 version:', pybind11.__version__)"
echo [A053] CMake:   %CMAKE%
"%CMAKE%" --version | findstr /B /C:"cmake version"
echo [A053] Ninja:   %NINJA%
"%NINJA%" --version

echo [A053] Configuring native module...
"%CMAKE%" --fresh -S cpp -B build -G Ninja ^
  -DCMAKE_BUILD_TYPE=Release ^
  "-Dpybind11_DIR=%PYBIND11_CMAKE_DIR%" ^
  -DPYBIND11_FINDPYTHON=ON ^
  "-DPython_EXECUTABLE=%PY%" ^
  "-DPython3_EXECUTABLE=%PY%"
if errorlevel 1 (
    echo [ERROR] CMake configure failed.
    echo [HINT] If the next error concerns linking Python with Strawberry/MinGW,
    echo        run this from an x64 Visual Studio Developer Command Prompt so
    echo        CMake can use MSVC instead of Strawberry GCC.
    exit /b 18
)

echo [A053] Building native module...
"%CMAKE%" --build build --config Release --parallel
if errorlevel 1 (
    echo [ERROR] Native build failed.
    echo [HINT] If the linker rejects Python import libraries under GNU/MinGW,
    echo        use an x64 Visual Studio Developer Command Prompt and rerun.
    exit /b 19
)

echo [A053] Staging native runtime dependencies...
"%PY%" tools\stage_native_runtime.py
if errorlevel 1 (
    echo [ERROR] Failed to stage/diagnose native runtime dependencies.
    exit /b 20
)

echo [A053] Native build completed successfully.
exit /b 0
