@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo SST Katlas Source Crawler v0.2.2 - RDF ONLY
echo Output: Katlas_Sources_v0.2.2_Outputs
echo ============================================================
if not exist .venv\Scripts\python.exe (
  echo [1/3] Creating virtual environment...
  py -3 -m venv .venv || exit /b 1
) else (
  echo [1/3] Virtual environment already exists.
)
echo [2/3] Downloading/updating official Katlas RDF datasets...
.venv\Scripts\python.exe -m katlas_source.cli --config config.json download || exit /b 1
echo [3/3] Building knots + links export...
.venv\Scripts\python.exe -m katlas_source.cli --config config.json build || exit /b 1
echo RDF export complete.
