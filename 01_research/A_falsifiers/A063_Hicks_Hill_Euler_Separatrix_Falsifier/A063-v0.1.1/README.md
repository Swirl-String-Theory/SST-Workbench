# A063 Hicks-Hill Euler Separatrix Falsifier v0.1.1

Analytical qualification release. **Not a canonical SST Falsifier Framework v1.0.7 instance, nor a mass/electron or finite-core-stability certification.** No old falsifier or v0.1.0 data is modified. v1.0.7 native certification is explicitly `UNRESOLVED` (H8).

## Improvements over v0.1.0

- H2/H3/H4 independently test Hill, Hicks-Beltrami and Hicks-zero-translation Euler/divergence with four finite-difference resolutions; no cross-family mixing of maxima.
- H5/H6 scan 121 latitude points across the spherical separatrix in each flow, at radial offsets 1e-3, 1e-4 and 1e-5, tracking velocity and pressure matching.
- H7A solves the toroidal winding root W=3/4 in the first Beltrami flow and performs continuous 4-meridional-cycle orbit integration to check 3D closure. It establishes a **numerical candidate** for a T(3,4) streamline, not a certified knotted vortex tube.
- H7 and H7B remain UNRESOLVED. In particular trefoil T(2,3) is neither verified nor globally excluded.
- H8 remains UNRESOLVED; C++ FP64 / official Framework v1.0.7 not executed.
- H9/H10 provide analytic checks for A046 and A057, respectively; no E013 carriers are replaced.

## Run

Requirements: Python 3.10+, `numpy`, `scipy`, `pytest`, and for the independent report generator `reportlab` or LaTeX.

Windows from the instance root:

```bat
py -3 -m pip install -r requirements.txt
run_all.cmd SELFTEST
run_all.cmd FULL
```

Linux/macOS:

```sh
python -m pip install -r requirements.txt
python -m pytest tests -q
python run_hicks.py
```

`run_all.cmd FULL` writes its versioned output folder, then renders the independent external PDF and the scientific PDF into `../A063-v0.1.1_external_reports/`. The unmodified external report-generator in `04_tools/D_proof/SST_Falsifier_Report_Generator` can produce a post-hoc PDF from those outputs. An enriched scientific PDF is also included as a release artifact.

## Scientific restrictions

The observed 3/4 line-winding and 3D closure of a trajectory on a smooth invariant torus support a T(3,4) **candidate** only. Finite sampling and closure tolerances do not establish topological certification, structural stability, a knotted core, or a stable particle. Negative trefoil claims require global interval bounding and independently computed topological invariants.

The source seal is a release-side SHA-256 consistency check, **not** the framework v1.0.7 `FREEZE` commitment.

The full source bundle also retains source/protocol SHA checks in `SOURCE_SEAL.json`, an immutable v0.1.0 archive hash at the integration root, and an independent scientific report including exact formulas and allowed interpretations.
