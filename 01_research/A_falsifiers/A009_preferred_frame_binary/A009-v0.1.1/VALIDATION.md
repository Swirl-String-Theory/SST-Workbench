# Validation — v0.1.1

Validation date: 2026-08-07

## Environment result

- `python -m compileall -q .`: **PASS**
- `python -m pytest -q`: **12 passed**
- `python run_all_checks.py --out-dir audit_out`: **all 9 internal checks passed**
- `python run_ideal_database.py --all-knots --all-links --no-linking`: **PASS**
- Native C++ source and hash-rebuild loader are included. The packaging sandbox does not contain `pybind11`, so native compilation could not be exercised here; all Python fallback paths were exercised.

Local native preflight:

```bat
python -m pip install pybind11
python -m sst_pf_binary_falsifier.build_ext_if_needed --force --strict
python run_all_checks.py --force-build --out-dir audit_out_native
python -m pytest -q
```

## Gilbert database ingestion

The exact supplied compressed files are bundled in `data/` and parsed directly.

| Quantity | Result |
|---|---:|
| `Ideal.txt.gz` knot records | 250 |
| `IdealLinks.txt.gz` link records | 130 |
| total Fourier curves audited | 553 |
| maximum absolute source-sampling length error | `2.5050625025e-05` |
| full catalog source-length audit | PASS |

The largest catalog reconstruction deviation is the analytic Hopf-link record `L2a1`; all knot records reproduce the stored source-sampling lengths to about `1.3e-6` relative or better.

### Trefoil `3:1:1`

Stored source value:

```text
L/D = 16.371637
D   = 1
```

At the database's 512-point convention the Fourier reconstruction gives

```text
L = 16.3716383074107
relative error = +7.9858277e-08
```

With `sst_core` scaling,

```text
D = 2*r_c = 2.81794034e-15 m
L_target = 4.613429633413658e-14 m
```

The 72-point dynamical baseline run remains Galilean invariant within numerical precision:

```text
chi0 = 0
chi2 = 0
max energy relative deviation = 0
max shape relative deviation = 5.3861e-16
baseline = PASS
```

### Hopf link `L2a1`

Both `STRING` components are retained as independent closed filaments. At the source 256-point convention the topology audit gives

```text
Gauss linking number = -1.0001004074
nearest integer      = -1
```

A 48+48 point multi-component drift run gives

```text
chi0 = -1.3810e-12
chi2 = +1.3141e-12
max energy relative deviation = 2.5533e-16
max shape relative deviation = 3.0565e-16
baseline = PASS
```

The tiny fitted `chi` values are numerical noise around the exact Galilean baseline, not an SST preferred-frame prediction.

## Internal check results

| Check | Result |
|---|---|
| single-filament backend parity harness | PASS |
| Ideal.txt / IdealLinks parser + Fourier convention | PASS |
| multi-component link backend parity harness | PASS |
| Galilean uniform-drift baseline | PASS |
| synthetic `chi0/chi2` recovery | PASS |
| universal vs non-universal `q/m` controls | PASS |
| homogeneous linear Euler no-bulk-wave structural gate | PASS |
| J1738 reference correction reconstruction | PASS |
| energy-balance pass/fail controls | PASS |

## Scientific status

This patch materially improves the geometry input: the preferred-frame experiment can now run on the supplied ideal Fourier knots and multi-component links instead of only an analytic torus-knot seed.

It still does **not** create an SST preferred-frame effect by assumption. A nonzero physical `chi0` or `chi2` requires an independently specified SST constitutive/clock/background closure beyond homogeneous Galilean-invariant Euler flow.
