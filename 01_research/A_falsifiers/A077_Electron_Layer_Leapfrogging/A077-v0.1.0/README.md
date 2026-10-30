# ID_PENDING-v0.1.0 — Electron Layer & Leapfrogging Unknots

REAL SST Falsifier Framework v1.1.0 self-contained `_sst_runtime/`: generated from a 140/140 verified release. This is a NEW, unregistered catalog candidate; verify ID before copying to Workbench. Do not overwrite old versions.

**Scientific status: DEVELOPMENT_DIAGNOSTIC_ONLY**. The ring solver tests softened mutual induction of coaxial unknots and an approximate thin-core self-speed. It is not a 3D full-Euler finite-core model and cannot infer electron spin-1/2 or intrinsic quantized levels. G3, G4, G7 and G8 remain unresolved.

## Windows commands

1. `python -m pip install numpy scipy matplotlib pytest pybind11 setuptools reportlab` (plus a local LaTeX installation for normal PDF reports).
2. `run_all.cmd BACKEND_PREFLIGHT` (requires Visual Studio/MSVC toolchain).
3. `python -m pytest -q tests`
4. `run_all.cmd FREEZE`
5. `run_all.cmd BASIC`
6. `run_all.cmd FULL`
7. `run_all.cmd CERTIFY` (may return 3 when physical-science gates are unresolved; do not bypass).

With `cpu` profile, real independent Python and native `native_ext._sst_native.ring_integrate` C++ are the intended 2-of-3 scientific backends. The GPU science kernel is unimplemented; probe results never count. Previous runs remain separate and outputs are packaged BLIND with SHA-256. Full 16-section LaTeX report is present. `ATLAS_VERIFY` is not needed: analytic control opts out of E010 atlas.

You can run `python -m science.run_science --cpp` after compiling `native/ring_cli.cpp` as an optional separate CLI parity diagnostic. This cannot replace the framework native backend.

Do not publish private/ or reveal keys. Generated instance should never be transplanted into a frozen existing family without a catalog audit.
