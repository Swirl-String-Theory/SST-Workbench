# A065 v0.3.2 — Fixed-core convergence and independent Fremlin simulation provider

**SST Falsifier Framework v1.0.7:** external, canonical frozen and unmodified. The generated instance is fresh and preregistered for every run.

**Windows:** `run_all.cmd QUALIFY` for the complete numerical tranche and self-contained PDF; `run_all.cmd FRAMEWORK` for the official framework FREEZE/FULL/reveal-policy; `run_all.cmd ALL` runs tests plus both scientific branches. On Linux: `bash run_all.sh QUALIFY`. Exports appear only under `exports/<unique run id>/` and never overwrite previous runs.

**Fremlin source required for genuine second geometry + native dynamic simulation:** default `C:\workspace\projects\SST-Workbench\03_data\A_knots\02_fourier\resources_swirl\3_1\knot.3_1u.short`; override with `SST_A065_FREMLIN_PATH`. The file must have registered E010 SHA-256. A C++17 compiler (`g++` or `CXX` override) is required. Missing or modified source -> `UNRESOLVED` or `FAIL`, not a synthetic stand-in.

`QUALIFY` numerically tests 75/150/300/600 source-derived grids at fixed ε=.12, Γ=1, T=.04, using RK4. The interpolated N600 grid is NOT independent raw data. Official framework G2 retains coarse 75→150 FAIL; G10 tests refined discretization, G11 tests the actual Fremlin C++-generated simulation. G5 remains kernel-only.

The solver and the full physics remain distinct: a different actual raw knot + C++ solver makes an independent **simulated filament-ODE data source**, but **does not prove** independent incompressible Euler PDE motion, quantum Casimir force, metal response, or gravity.

All three source datasets and their seals remain unchanged from v0.3.1-r1. New scientific protocol and runnable code have a versioned new precommit. The exported LaTeX is self-contained without external image/TeX includes. See `docs/QUALIFICATION_V032.md`.
