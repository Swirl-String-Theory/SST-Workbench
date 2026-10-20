@echo off
setlocal
cd /d "%~dp0"
python src\benchmark.py || exit /b 1
python -m unittest discover -s tests -v || exit /b 1
echo Done. Reports in report\ and gates in results\gate_results.json
