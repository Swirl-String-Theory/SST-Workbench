# SST Fermat / Knot Research Harness v0.1

Standalone research package based on `SST_cpp_pybind_audit_template`.
It does **not** import, patch, or modify SSTcore.

The package uses:

- Python for orchestration, sweeps, geometry, audit output, and plotting-ready JSON/CSV;
- a C++17 `pybind11` extension for radial-profile kernels and batch Biot--Savart sampling;
- a numerically equivalent Python fallback for audit parity and systems without a compiler.

## Scientific scope

Version 0.1 implements two deliberately separated levels:

1. **Radial certification** for candidate Fermat-critical radii of a resolved vortex profile,
   using
   \[
   S(x)=\sqrt{1-\beta(x)^2},\qquad R_F(x)=\frac{x}{S(x)},\qquad
   -x\beta\beta'=1-\beta^2,
   \]
   where \(x=r/r_c\) and \(\beta=u/c\).
2. **Local knot-tube scan** for torus-knot centerlines using a regularized midpoint
   Biot--Savart field. This reports local transverse minima of \(\rho/S\); it does **not**
   certify a global closed Fermat geodesic or a quasinormal mode.

The code therefore distinguishes:

- `RADIAL_FERMAT_CRITICAL_CANDIDATE`;
- `LOCAL_TRANSVERSE_MINIMUM_CANDIDATE`;
- a future `GLOBAL_CLOSED_FERMAT_ORBIT` certification, which is not implemented in v0.1.

## Canonical constants

```text
v_swirl = 1.09384563e6 m s^-1
r_c     = 1.40897017e-15 m
c       = 299792458 m s^-1
Gamma_0 = 2*pi*r_c*v_swirl
```

All native calculations are dimensionless unless a result is explicitly converted to SI.

## Layout

```text
SST_fermat_pybind_research_v0.1/
├── README.md
├── pyproject.toml
├── requirements.txt
├── run_profile.py
├── run_sweep.py
├── run_knot_scan.py
├── run_all_checks.py
├── cpp/
│   ├── fermat_kernel.hpp
│   └── native.cpp
├── fermat_ext/
│   ├── __init__.py
│   ├── _config.py
│   ├── build_ext_if_needed.py
│   ├── constants.py
│   ├── core.py
│   ├── fallback.py
│   └── knot_scan.py
├── tests/
│   └── test_kernel.cpp
└── examples/
    ├── minimal_commands.txt
    └── full_commands.txt
```

## Quick start

```bash
cd SST_fermat_pybind_research_v0.1
python -m pip install -r requirements.txt

# Build the optional C++ backend.
python -m fermat_ext.build_ext_if_needed --force --strict

# Analytic 1/r benchmark.
python run_profile.py --profile external --a-core-over-rc 0.0045

# Scan resolved core radii around the formal window.
python run_sweep.py --profile rankine \
  --a-values 0.0038,0.0042,0.0048,0.0052,0.0060

# Local transverse scan around a T(2,3) trefoil centerline.
python run_knot_scan.py --p 2 --q 3 --centerline-points 240 \
  --stations 12 --angles 16 --radial-samples 120

# C++/Python parity and scientific guard checks.
python run_all_checks.py --out-dir audit_out
```

If the native extension cannot be built, all commands fall back to Python. Use
`--force-python` to audit the fallback explicitly.

## Profiles

- `external`: \(\beta=\beta_0/x\), with `a_core_over_rc` used only as a validity cutoff;
- `rankine`: solid-body interior matched continuously to \(\beta_0/x\);
- `rosenhead`: \(\beta=\beta_0x/(x^2+a^2)\);
- `lamb_oseen`: \(\beta=\beta_0[1-e^{-x^2/(2a^2)}]/x\).

No profile is Canon by inclusion in this package. They are controlled Research-Track probes.

## Audit semantics

A radial result is accepted only when:

- \(S>0\) at the candidate;
- the root is outside the declared vorticity-core radius;
- the result converges under scan refinement;
- native and Python backends agree within the configured tolerance.

The knot scan is weaker. It reports local radial-plane minima but explicitly sets
`global_closed_orbit_certified=false`.

## Template review incorporated

Relative to the original template, this fork:

- removes prebuilt `.pyd`, `__pycache__`, and machine-specific stamp files;
- hashes all `cpp/*.cpp` and `cpp/*.hpp` files, not one source only;
- attempts to import an existing extension even when auto-build is disabled;
- records build/import errors instead of silently discarding them;
- adds result schema and package versions;
- keeps Python/C++ parity as an explicit audit gate;
- separates research classifications from numerical success.

## v0.1.1 Windows/setuptools hotfix

This release explicitly declares `fermat_ext` as the only Python package in both the generated build script and `pyproject.toml`. This prevents recent setuptools versions from interpreting `cpp/` and `audit_out/` as additional top-level packages during `build_ext --inplace`.

After replacing v0.1, run:

```bash
python -m fermat_ext.build_ext_if_needed --force --strict
```

The `--force` flag regenerates `build/_setup__fermat_native.py`; deleting `build/` is optional.
