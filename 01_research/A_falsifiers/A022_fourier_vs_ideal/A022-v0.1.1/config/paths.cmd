@echo off
rem SST Workbench defaults. Override any variable before calling a run_*.cmd.
if not defined SST_FVI_BASE set "SST_FVI_BASE=..\.."
if not defined SST_FVI_FSERIES set "SST_FVI_FSERIES=%SST_FVI_BASE%\KnotPlot\Knots_FourierSeries"
if not defined SST_FVI_RELAXED set "SST_FVI_RELAXED=%SST_FVI_BASE%\KnotPlot\knots\final"
rem Optional explicit ideal source. Leave blank to use the built-in Workbench source resolver.
if not defined SST_FVI_IDEAL set "SST_FVI_IDEAL="
if not defined SST_FVI_IDEAL_JS set "SST_FVI_IDEAL_JS="
