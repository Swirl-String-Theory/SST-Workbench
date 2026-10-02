@echo off
setlocal
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe scripts\run_qm.py --preset quick --require-native --ids L2a1 L4a1 L5a1 L6a4 L6n1 L7n1 %*
) else (
  python scripts\run_qm.py --preset quick --require-native --ids L2a1 L4a1 L5a1 L6a4 L6n1 L7n1 %*
)
