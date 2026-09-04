# SST Chiral Kelvin v0.1.2 Patch Notes

Numerical hardening drop-in on top of a validated v0.1.0/v0.1.1 tree.
Kernels (`native.cpp`, `core.py`, `fallback.py`, `_config.py`,
`build_ext_if_needed.py`) are unchanged.

## Patch contents

- `chiral_kelvin/convergence.py` — near-degenerate clustering, core
  `\eta_a` gate, Fourier fingerprints, eigen-conditioning, separate
  numerical vs physical gates
- `chiral_kelvin/__init__.py` — version `0.1.2` + new exports
- `run_all_checks.py` — baseline + convergence with presets
- `run_resolution_ladder.py` — ladder-only CLI
- `run_all_v012.cmd` — CMD entrypoint
- `CHANGELOG.md`

## First run

Do **not** start with `max`. Use:

```bat
run_all_v012.cmd quick
```

Preset resolutions:

| preset | N |
|--------|---|
| `quick` | 48, 64, 96 |
| `full` | 64, 96, 128 |
| `max` | 128, 192, 256 |

After `quick` succeeds technically:

```bat
run_all_v012.cmd full
```

Only then:

```bat
run_all_v012.cmd max
```

`max` is substantially heavier (dense `2N×2N` operator + eigendecomposition).

## Key outputs to inspect after `quick`

```text
audit_out_v012/audit_summary_v0.1.2.json
audit_out_v012/convergence_v012/convergence_summary_v0.1.2.json
audit_out_v012/convergence_v012/core_resolution.csv
audit_out_v012/convergence_v012/trefoil_N64_to_N96_cluster_convergence.csv
```

Gates:

- `implementation_ok` — baseline null checks + matcher self-check
- `numerical_tracking_ready` — stable N→N' cluster tracking
- `physical_interpretation_ready` — trackable **and** core `RESOLVED`

`implementation PASS` does not imply physical mode readiness.
