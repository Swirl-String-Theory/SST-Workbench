@echo off
setlocal EnableExtensions
set "KP_SHORTCUT=C:\workspace\solo\_projects\SST-Workbench\KnotPlot\KnotPlot.lnk"
set "MATRIX_DIR=C:\workspace\solo\_projects\SST-Workbench\KnotPlot\KnotPlot_3p1_MultiDynamics_Relaxation_Matrix_v0.1.0"
set "MASTER=%MATRIX_DIR%\98_run_core_matrix.kpc"
set "LOG=%MATRIX_DIR%\core_matrix_console.log"

if not exist "%KP_SHORTCUT%" (
  echo ERROR: KnotPlot shortcut not found:
  echo   %KP_SHORTCUT%
  exit /b 1
)
if not exist "%MATRIX_DIR%" (
  echo ERROR: Matrix directory not found:
  echo   %MATRIX_DIR%
  exit /b 1
)
if not exist "%MASTER%" (
  echo ERROR: Master KPC not found:
  echo   %MASTER%
  exit /b 1
)

for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%KP_SHORTCUT%'); [Console]::Write($s.TargetPath)"`) do set "KP_EXE=%%I"
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%KP_SHORTCUT%'); [Console]::Write($s.WorkingDirectory)"`) do set "KP_WORKDIR=%%I"
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%KP_SHORTCUT%'); [Console]::Write($s.Arguments)"`) do set "KP_ARGS=%%I"

if not defined KP_EXE (
  echo ERROR: Could not resolve TargetPath from KnotPlot.lnk
  exit /b 1
)
if not exist "%KP_EXE%" (
  echo ERROR: Resolved KnotPlot executable not found:
  echo   %KP_EXE%
  exit /b 1
)
if not defined KP_WORKDIR set "KP_WORKDIR=C:\workspace\solo\_projects\SST-Workbench\KnotPlot"

echo ============================================================
echo KnotPlot 3.1 CORE Multi-Dynamics Relaxation Matrix
echo ============================================================
echo Shortcut : %KP_SHORTCUT%
echo Target   : %KP_EXE%
echo Start in : %KP_WORKDIR%
echo Master   : %MASTER%
echo Output   : %MATRIX_DIR%
echo Log      : %LOG%
echo ============================================================

pushd "%KP_WORKDIR%" || exit /b 1
"%KP_EXE%" %KP_ARGS% -nog ^< "%MASTER%" ^> "%LOG%" 2^>^&1
set "RC=%ERRORLEVEL%"
popd

echo.
echo KnotPlot finished with exit code %RC%.
echo Log: %LOG%
exit /b %RC%
