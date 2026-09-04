@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install -e . --no-build-isolation
py -3 -m sst21d build-native
py -3 -m sst21d static --database examples\ideal_mini.txt --samples 256 --metadata data\sst21_metadata_seed.csv --out outputs\demo_static --require-native
py -3 -m sst21d make-demo-trajectory --out examples\demo_trajectory.npz
py -3 -m sst21d dynamic --trajectory examples\demo_trajectory.npz --topology-key 0_1 --time-unit s --length-unit m --out outputs\demo_dynamic
pause
