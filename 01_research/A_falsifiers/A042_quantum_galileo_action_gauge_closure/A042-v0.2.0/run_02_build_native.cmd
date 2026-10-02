@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo [2/9] Build C++17 / pybind11 native backend
echo ============================================================

call .venv\Scripts\activate.bat
if errorlevel 1 (
  echo ERROR: failed to activate .venv.
  exit /b 1
)

REM Prefer an already initialized MSVC environment.
where cl >nul 2>nul
if not errorlevel 1 goto :compiler_ready

REM Visual Studio 2026 Community - added without removing VS2022.
set "VS2026_VCVARS=C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat"
if exist "%VS2026_VCVARS%" (
  echo Trying Visual Studio 2026 Community x64...
  call "%VS2026_VCVARS%" x64 >nul
  where cl >nul 2>nul
  if not errorlevel 1 goto :compiler_ready

  echo Trying Visual Studio 2026 Community x86_amd64...
  call "%VS2026_VCVARS%" x86_amd64 >nul
  where cl >nul 2>nul
  if not errorlevel 1 goto :compiler_ready
)

REM Preserve Visual Studio 2022 Community support.
set "VS2022_VCVARS=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
if exist "%VS2022_VCVARS%" (
  echo Trying Visual Studio 2022 Community x64...
  call "%VS2022_VCVARS%" x64 >nul
  where cl >nul 2>nul
  if not errorlevel 1 goto :compiler_ready

  echo Trying Visual Studio 2022 Community x86_amd64...
  call "%VS2022_VCVARS%" x86_amd64 >nul
  where cl >nul 2>nul
  if not errorlevel 1 goto :compiler_ready
)

REM BuildTools fallbacks for both generations.
set "VS2026_BT_VCVARS=C:\Program Files\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
if exist "%VS2026_BT_VCVARS%" (
  echo Trying Visual Studio 2026 BuildTools x64...
  call "%VS2026_BT_VCVARS%" x64 >nul
  where cl >nul 2>nul
  if not errorlevel 1 goto :compiler_ready
  echo Trying Visual Studio 2026 BuildTools x86_amd64...
  call "%VS2026_BT_VCVARS%" x86_amd64 >nul
  where cl >nul 2>nul
  if not errorlevel 1 goto :compiler_ready
)

set "VS2022_BT_VCVARS=C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
if exist "%VS2022_BT_VCVARS%" (
  echo Trying Visual Studio 2022 BuildTools x64...
  call "%VS2022_BT_VCVARS%" x64 >nul
  where cl >nul 2>nul
  if not errorlevel 1 goto :compiler_ready
  echo Trying Visual Studio 2022 BuildTools x86_amd64...
  call "%VS2022_BT_VCVARS%" x86_amd64 >nul
  where cl >nul 2>nul
  if not errorlevel 1 goto :compiler_ready
)

echo.
echo ERROR: no usable MSVC cl.exe was found.
echo Checked existing PATH plus VS2026 and VS2022 Community and BuildTools.
exit /b 1

:compiler_ready
echo.
echo Using compiler:
where cl
cl 2>&1 | findstr /C:"Microsoft (R) C/C++ Optimizing Compiler"

REM Use the already validated environment; do not let setuptools call vcvarsall again.
set DISTUTILS_USE_SDK=1
set MSSdk=1

echo.
echo Building native extension...
python setup.py build_ext --inplace
if errorlevel 1 (
  echo.
  echo ERROR: native build failed.
  echo Review the build output above for the actual cause.
  exit /b 1
)

python -c "import sst_qgi_native; print('native backend: cpp-pybind11')"
if errorlevel 1 (
  echo ERROR: native extension was built but could not be imported.
  exit /b 1
)
endlocal
