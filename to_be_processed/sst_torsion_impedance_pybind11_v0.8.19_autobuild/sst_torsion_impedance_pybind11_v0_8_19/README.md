# SST Core--Torsion Impedance Matching Audit

Standalone research-track pybind11 build for the Core--Torsion Impedance Matching Lemma.

This package is intentionally outside `SSTcore`. It is an experimental falsification/audit module, not a canonized SSTcore API surface.

## What it computes

For a closed polygonal knot centerline `K`, the extension computes the raw transverse torsion/shear inertia tensor

```text
M_T = zeta * rho_T * pi*a^2 * integral_K (I - t(s)t(s)^T) ds
```

and the diagnostic residual

```text
chi_K^(T) = c_T^2 * lambda_iso(M_T) / (2 E0[K])
lambda_iso = trace(M_T)/3
```

No matching is imposed. The output reports the scale/density required to force `chi=1` separately.

## Install

```bash
python -m pip install --upgrade pip setuptools wheel pybind11 numpy pytest
python -m pip install -e .
```

## Run analytic smoke tests

```bash
python audit_impedance.py --analytic --n 2048
python test_impedance.py
```

## Run against SSTcore `ideal.txt`

Use an existing `ideal.txt` from SSTcore, without copying this module into SSTcore:

```bash
python audit_impedance.py --ideal C:\workspace\projects\SST-Workbench\knots_ideal_favorites.txt --n 4096 --json impedance_results.json
```

The script supports AB ids `3:1:1` and `4:1:1` by default.

## C++ CLI smoke test without pybind11

The same source can compile as a tiny standalone C++ CLI when `BUILD_PYBIND11_MODULE` is not defined:

```bash
g++ -std=c++17 -O2 src/sst_torsion_impedance.cpp -o impedance_cli
./impedance_cli
```

## Status

`[RESEARCH-TRACK]`. Keep outside SSTcore until the impedance/dressing scale is derived rather than fitted.

## Autobuild workflow

This package includes `sst_torsion_impedance_build.py`, matching the compact local-build pattern used in the SST trefoil Biot--Savart package.

```bash
python sst_torsion_impedance_build.py          # build only if missing/stale
python sst_torsion_impedance_build.py --force  # force rebuild
python sst_torsion_impedance_build.py --clean  # remove build temp/header extraction dirs
```

`audit_impedance.py` and `test_impedance.py` call this helper automatically. If `src/sst_torsion_impedance.cpp` is newer than the compiled `.so`/`.pyd`, or if no extension exists, it rebuilds in-place before import.

Header resolution order:

1. use extracted `_pybind11_include/pybind11/pybind11.h` when already present;
2. extract `pybind11_headers.zip` if bundled next to the build helper;
3. otherwise use `pybind11.get_include()` from an installed `pybind11` package.