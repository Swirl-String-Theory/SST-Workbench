# A065-v0.3.4 — Historical Fourier/Torus Trefoil Extension

Extends v0.3.3 (all three original data seals byte-identical).

Command (Windows): `run_all.cmd VERIFY`, `run_all.cmd SELFTEST`, `run_all.cmd HISTORY`, `run_all.cmd PARITY`, `run_all.cmd ALL`.

HISTORY scans the four original N600/N1200 historical XYZ files and analytic formulas, runs C++17 RK4 and Python spot parity, and produces a blind PDF, TeX and JSON.

Requirements: Python 3.10+, C++17 `g++` in PATH for full historical simulation. LaTeX `pdflatex` optional; pure Python fallback PDF available. No NumPy required. Framework ALL/FULL needs separate untouched frozen v1.0.7 installation.

Important: original 2015 shapes are initial geometries only; all outputs dimensionless, no physical SST mass, gravity, or Casimir claim. Original G2 failure preserved and G11/Fremlin remains separately falsifiable.

See `docs/HISTORICAL_V034_CONTRACT.md`.
