@echo off
rem SST Workbench central path include (SP01).
rem Override any SST_* variable before calling this file or a run_*.cmd.
rem Usage:  call "%SST_WORKBENCH_ROOT%\07_scripts\paths.cmd"
rem     or: call "<path-to-this-file>\paths.cmd"

if not defined SST_WORKBENCH_ROOT call :find_root
if not defined SST_WORKBENCH_ROOT (
  echo ERROR: SST_WORKBENCH_ROOT not set and .sst-workbench-root not found. 1>&2
  exit /b 1
)

if not defined SST_DATA_ROOT set "SST_DATA_ROOT=%SST_WORKBENCH_ROOT%\03_data"

if not defined SST_KNOT_DATASET (
  if exist "%SST_DATA_ROOT%\A_knots\04_knotplot\final\" (
    set "SST_KNOT_DATASET=%SST_DATA_ROOT%\A_knots\04_knotplot\final"
  ) else if exist "%SST_WORKBENCH_ROOT%\KnotPlot\knots\final\" (
    set "SST_KNOT_DATASET=%SST_WORKBENCH_ROOT%\KnotPlot\knots\final"
  ) else (
    set "SST_KNOT_DATASET=%SST_DATA_ROOT%\A_knots\04_knotplot\final"
  )
)

if not defined SST_IDEAL_SOURCES (
  if exist "%SST_DATA_ROOT%\A_knots\01_ideal\ideal_sources\" (
    set "SST_IDEAL_SOURCES=%SST_DATA_ROOT%\A_knots\01_ideal\ideal_sources"
  ) else if exist "%SST_WORKBENCH_ROOT%\Ideal_Sources\" (
    set "SST_IDEAL_SOURCES=%SST_WORKBENCH_ROOT%\Ideal_Sources"
  ) else (
    set "SST_IDEAL_SOURCES=%SST_DATA_ROOT%\A_knots\01_ideal\ideal_sources"
  )
)

if not defined SST_KATLAS_SOURCES (
  if exist "%SST_DATA_ROOT%\A_knots\03_katlas\v0.2.2\" (
    set "SST_KATLAS_SOURCES=%SST_DATA_ROOT%\A_knots\03_katlas\v0.2.2"
  ) else if exist "%SST_WORKBENCH_ROOT%\Katlas_Sources_v0.2.2_Outputs\" (
    set "SST_KATLAS_SOURCES=%SST_WORKBENCH_ROOT%\Katlas_Sources_v0.2.2_Outputs"
  ) else (
    set "SST_KATLAS_SOURCES=%SST_DATA_ROOT%\A_knots\03_katlas\v0.2.2"
  )
)

if not defined SST_FSERIES_ROOT (
  if exist "%SST_DATA_ROOT%\A_knots\02_fourier\knotplot_legacy\" (
    set "SST_FSERIES_ROOT=%SST_DATA_ROOT%\A_knots\02_fourier\knotplot_legacy"
  ) else if exist "%SST_WORKBENCH_ROOT%\KnotPlot\Knots_FourierSeries\" (
    set "SST_FSERIES_ROOT=%SST_WORKBENCH_ROOT%\KnotPlot\Knots_FourierSeries"
  ) else if exist "%SST_WORKBENCH_ROOT%\Fremlin_FourierSeries\" (
    set "SST_FSERIES_ROOT=%SST_WORKBENCH_ROOT%\Fremlin_FourierSeries"
  ) else (
    set "SST_FSERIES_ROOT=%SST_DATA_ROOT%\A_knots\02_fourier\knotplot_legacy"
  )
)

exit /b 0

:find_root
set "_SWP_CUR=%~dp0"
:find_root_loop
if exist "%_SWP_CUR%.sst-workbench-root" (
  for %%I in ("%_SWP_CUR%.") do set "SST_WORKBENCH_ROOT=%%~fI"
  set "_SWP_CUR="
  exit /b 0
)
for %%I in ("%_SWP_CUR%..") do set "_SWP_NEXT=%%~fI\"
if /I "%_SWP_NEXT%"=="%_SWP_CUR%" (
  set "_SWP_CUR="
  set "_SWP_NEXT="
  exit /b 1
)
set "_SWP_CUR=%_SWP_NEXT%"
set "_SWP_NEXT="
goto :find_root_loop
