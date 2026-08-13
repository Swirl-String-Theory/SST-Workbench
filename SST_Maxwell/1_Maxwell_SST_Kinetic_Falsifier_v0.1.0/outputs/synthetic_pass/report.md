# Maxwell–SST falsifier report — synthetic-pass-demo

**Dataset:** `synthetic`  
**Verdict:** `DEMO_ONLY`

> Absence of a triggered falsifier is **not** validation of SST.

## Conditions

- T = 300 K
- kBT = 0.0258519998 eV
- observation time = 0.001 s
- drive energy = 10 eV

## Physical falsifiers

- None triggered by the supplied data.

## Numerical / closure failures

- None triggered by the supplied data.

## Mode ledger

| Knot | Mode | Family | Gap eV | Coupling | tau s | 3-gate active | Gap claim fail |
|---|---|---|---:|---:|---:|---|---|
| 3_1 | orient_0 | orientation | 0.0 | 0.02 | 1e-06 | True | False |
| 3_1 | kelvin_1 | kelvin | 2.0 | 0.01 | 2e-06 | True | False |
| 3_1 | twist_1 | twist | 5.0 | 0.005 | 4e-06 | True | False |
| 3_1 | core_1 | core | 20.0 | 0.002 | 8e-06 | False | False |
| 3_1 | writhe_obs | writhe | 0.0 | 0.0 |  | None | False |

## Thermodynamics

| Knot | Cv/kB | Limit | Status |
|---|---:|---:|---|
| 3_1 | 3.0170358e-30 | 1e-06 | PASS |

## Spectroscopy

| Observable | Bound eV | Empirical limit eV | Status |
|---|---:|---:|---|
| line_A | 2e-15 | 1e-09 | PASS |

## Canonical scale checks

- 0.5 rho_f v_swirl^2 = 418774.392 Pa
- v_swirl/r_c = 7.76344066e+20 s^-1
- These are scale checks only, not a knot-gas pressure or a mode gap.
