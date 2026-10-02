@echo off
rem NOTE: intentionally no SETLOCAL. This script exports MSVC variables to caller.

where cl.exe >nul 2>nul
if not errorlevel 1 goto :ready

set "VCVARS="
set "VSROOT="
set "VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"

if exist "%VSWHERE%" (
  for /f "usebackq delims=" %%I in (`"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "VSROOT=%%I"
)

if defined VSROOT if exist "%VSROOT%\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARS=%VSROOT%\VC\Auxiliary\Build\vcvarsall.bat"

rem Fallbacks, including the VS 2026/18 layout observed on the target workstation.
if not defined VCVARS if exist "%ProgramFiles%\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARS=%ProgramFiles%\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvarsall.bat"
if not defined VCVARS if exist "%ProgramFiles%\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARS=%ProgramFiles%\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
if not defined VCVARS if exist "%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARS=%ProgramFiles%\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
if not defined VCVARS if exist "%ProgramFiles%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" set "VCVARS=%ProgramFiles%\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"

if not defined VCVARS (
  echo ERROR: MSVC cl.exe is not on PATH and vcvarsall.bat could not be located.
  exit /b 1
)

if not exist build mkdir build >nul 2>nul
echo [PFD] Initializing MSVC directly: "%VCVARS%"
call "%VCVARS%" x86_amd64 > "build\vcvarsall.log" 2>&1
set "VCVARS_RC=%ERRORLEVEL%"

rem Some vcvarsall installations return a nonzero code after harmless missing-path
rem diagnostics. The actual gate is whether the compiler/linker environment exists.
where cl.exe >nul 2>nul
if errorlevel 1 (
  echo ERROR: vcvarsall did not expose cl.exe. See build\vcvarsall.log
  exit /b 1
)
where link.exe >nul 2>nul
if errorlevel 1 (
  echo ERROR: vcvarsall did not expose link.exe. See build\vcvarsall.log
  exit /b 1
)
if not "%VCVARS_RC%"=="0" echo [PFD] NOTE: vcvarsall returned %VCVARS_RC%, but cl.exe/link.exe are valid; continuing.

:ready
set "DISTUTILS_USE_SDK=1"
set "MSSdk=1"
for /f "delims=" %%I in ('where cl.exe 2^>nul') do if not defined PFD_CL set "PFD_CL=%%I"
echo [PFD] MSVC compiler: %PFD_CL%
exit /b 0
