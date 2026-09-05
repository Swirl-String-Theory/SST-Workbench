# Validation record for v0.2.1

v0.2.1 is a source-only upgrade of the v0.2.0 release: thickness-admissibility gates, arclength self-contact exclusion, iterative contact-graph union-find, and arclength-weighted geometry quantiles. The platform-specific native binary is still intentionally excluded from the release ZIP; rebuild locally from `cpp/native.cpp`.

## Automated tests

```text
see validation/pytest.txt
```

Coverage includes the v0.2.0 suite plus:

- arclength-exclusion self-contact on the Hopf link (coverage must be 0, not 1);
- iterative union-find on a 5000-edge contact chain;
- `weighted_quantile`, `curvature_spectral_tail`, diameter-scaled ropelength;
- `thickness_gate` on the Hopf link and a curvature-binding synthetic case;
- `curvature_mode_convergence` on a pure Fourier circle.

Native/Python parity tests skip on hosts without a C++ toolchain/`pybind11` build; they remain part of the suite and are expected to pass after `build-native --force --strict`.

## Strict-native campaign validation

Inherited from the v0.2.0 validation host (not re-run for this patch release):

- Smoke set: `L2a1`, `L6a4`, `L7n2` — 3/3 completed.
- Full preregistered quick set — 18/18 completed.
- Native parity gate — passed.
- Campaign failures — zero.

Re-run a campaign with `--no-resume` (or a fresh output directory) after upgrading: the suite version bump to `0.2.1` invalidates prior `run_signature` values so stale per-link JSON without G9 fields is not resumed.

## Native benchmark

Representative case (unchanged from v0.2.0):

```text
link: L6a4
components: 3
samples per component: 192
circulation sectors: 8
epsilon/D: 0.1
```

Measured on the validation container:

```text
C++ best:    0.002768616 s
NumPy best:  0.057902613 s
speedup:     20.9139x
max error:   2.220446049250313e-16
relative L2: 1.50621650914607e-16
```

This benchmark is hardware- and compiler-dependent; the parity error is the primary correctness result.
