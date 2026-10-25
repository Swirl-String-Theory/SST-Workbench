@echo off
setlocal
cd /d "%~dp0"
python test_gates.py || exit /b 1
for %%k in (0 1 2 3 4) do (python chunk_runner.py --chunk %%k --steps 3500 --N 288 --prefix main || exit /b 1)
python chunk_runner.py --chunk 0 --steps 3500 --N 192 --prefix n192 || exit /b 1
python chunk_runner.py --chunk 0 --steps 7000 --dt 0.0000075 --N 288 --prefix n288_halfdt || exit /b 1
for %%k in (0 1) do (python chunk_runner.py --chunk %%k --steps 3500 --N 384 --prefix n384 || exit /b 1)
for %%k in (0 1 2 3) do (python chunk_runner.py --chunk %%k --steps 2000 --N 512 --prefix n512 || exit /b 1)
for %%k in (0 1) do (python chunk_runner.py --chunk %%k --steps 2000 --dt 0.0000075 --N 512 --prefix n512_halfdt || exit /b 1)
python analyze_runs.py || exit /b 1
echo All reproducibility steps completed.
