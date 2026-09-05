# Validation — v0.1.0

Validation date: 2026-08-07

## Environment result

- `python -m pytest -q`: **8 passed**
- `python -m compileall -q .`: **PASS**
- `python run_all_checks.py --out-dir audit_out`: **all internal checks passed**
- Native C++ source and hash-rebuild loader are included, but the execution sandbox used for packaging did not contain `pybind11`; therefore native compilation could not be exercised here. The Python fallback was exercised fully. On a local environment with `pybind11` and a C++17 compiler, run:

```bash
python -m sst_pf_binary_falsifier.build_ext_if_needed --force --strict
python run_all_checks.py --force-build --out-dir audit_out_native
```

## Internal check results

| Check | Result |
|---|---|
| backend API/parity harness | PASS (Python fallback in packaging environment) |
| Galilean uniform-drift baseline | PASS |
| synthetic `chi0/chi2` recovery | PASS |
| universal vs non-universal `q/m` controls | PASS |
| homogeneous linear Euler no-bulk-wave structural gate | PASS |
| J1738 reference correction reconstruction | PASS |
| energy-balance pass/fail controls | PASS |

### Drift baseline

Default full audit returned

```text
chi0 = 0
chi2 = 0
max baseline relative energy deviation = 0
max translation-reduced shape deviation = 3.29e-16
```

This is the expected Galilean result for an unmodified incompressible Euler filament under uniform drift.

### Injected fit control

Injected:

```text
chi0 = +1.25
chi2 = -0.40
```

Recovered:

```text
chi0 = 1.249999999995949
chi2 = -0.39999999999999986
```

### PSR J1738+0333 reference reconstruction

Using the source values bundled in `data/j1738_reference.json`:

```text
Pdot_obs = -1.82e-14 s/s
Pdot_Shkl = +9.3e-15 s/s
Pdot_Gal = -3.0e-16 s/s
Pdot_corr = -2.72e-14 s/s
sigma_proxy = 2.57116705e-15 s/s
```

The uncertainty is a simple independent-Gaussian propagation and is not a replacement for the full timing posterior.

## Scientific status

The pack has validated the **audit machinery**, not SST itself. Publication-level SST falsification requires SST-generated inputs for one or more of:

- non-Euler drift response / `chi0`, `chi2`;
- object-by-object radiative/gravitational `q/m`;
- a genuine SST radiative far-field mode and flux;
- an independent radiation-reaction calculation;
- an SST binary `Pdot_b` prediction;
- an independently derived mapping to effective PPN preferred-frame coefficients.
