@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 1
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo ERROR: %PY% not found. Run run_00_setup.cmd first.
  goto :fail
)

if exist build\temp_native rmdir /s /q build\temp_native
set "VCVARS="
set "VSROOT="

rem 1) Reuse an already initialized VS environment when possible.
where cl.exe >nul 2>&1
if not errorlevel 1 goto :compiler_ready

rem 2) Prefer the VSINSTALLDIR already known to the parent shell.
if defined VSINSTALLDIR if exist "%VSINSTALLDIR%VC\Auxiliary\Build\vcvarsall.bat" set "VCVARS=%VSINSTALLDIR%VC\Auxiliary\Build\vcvarsall.bat"

rem 3) Discover Visual Studio/Build Tools using vswhere.
if not defined VCVARS (
  set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
  if exist "%VSWHERE%" (
    for /f "usebackq delims=" %%I in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSROOT=%%I"
    if defined VSROOT if exist "%VSROOT%\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARS=%VSROOT%\VC\Auxiliary\Build\vcvarsall.bat"
  )
)

rem 4) Conservative fallbacks for VS 2026/2022 editions.
if not defined VCVARS if exist "%ProgramFiles%\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARS=%ProgramFiles%\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat"
if not defined VCVARS if exist "%ProgramFiles%\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARS=%ProgramFiles%\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
if not defined VCVARS if exist "%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARS=%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
if not defined VCVARS if exist "%ProgramFiles%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARS=%ProgramFiles%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"

if not defined VCVARS (
  echo ERROR: Could not locate vcvarsall.bat.
  echo Install the MSVC x64/x86 build tools, or run from a Developer Command Prompt.
  goto :fail
)

echo [native] Initializing compiler with:
echo          "%VCVARS%"
call "%VCVARS%" x86_amd64 >nul
if errorlevel 1 (
  echo [native] WARNING: vcvarsall returned %ERRORLEVEL%. Checking whether cl.exe was nevertheless initialized...
)

:compiler_ready
where cl.exe >nul 2>&1 || (
  echo ERROR: cl.exe is not on PATH after Visual Studio initialization.
  goto :fail
)
where link.exe >nul 2>&1 || (
  echo ERROR: link.exe is not on PATH after Visual Studio initialization.
  goto :fail
)

for /f "delims=" %%I in ('where cl.exe') do if not defined CL_PATH set "CL_PATH=%%I"
echo [native] cl.exe: %CL_PATH%
cl.exe 2>&1 | findstr /I /C:"Version" >nul

rem Inherited v0.3.1+ fix:
rem Tell setuptools/distutils that the MSVC SDK is ALREADY initialized.
rem This prevents its internal `cmd /u /c vcvarsall.bat ... && set` bootstrap,
rem which is vulnerable to broken CMD AutoRun/path hooks on some Windows systems.
set "DISTUTILS_USE_SDK=1"
set "MSSdk=1"

"%PY%" setup_native.py build_ext --inplace --build-temp build\temp_native || goto :fail
"%PY%" -c "from sst_wp.native_ext import NATIVE_AVAILABLE; assert NATIVE_AVAILABLE; print('native backend loaded')" || goto :fail

popd
exit /b 0
:fail
set "RC=%ERRORLEVEL%"
if "%RC%"=="0" set "RC=1"
popd
exit /b %RC%
