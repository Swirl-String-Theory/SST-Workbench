# Maxwell–SST falsifier report — synthetic-fail-demo

**Dataset:** `synthetic`  
**Verdict:** `DEMO_ONLY`

> Absence of a triggered falsifier is **not** validation of SST.

## Conditions

- T = 300 K
- kBT = 0.0258519998 eV
- observation time = 1 s
- drive energy = 1 eV

## Physical falsifiers

- **FAIL [GAP]** `3_1/kelvin_bad`
- **FAIL [THERMODYNAMIC]** `3_1/`
- **FAIL [SPECTROSCOPIC]** `/line_fail`

## Numerical / closure failures

- **FAIL [CONVERGENCE]** `3_1/kelvin_bad`
- **FAIL [ENERGY_LEDGER]** `/e1`
- **FAIL [TAXONOMY]** `3_1/twist_bad`
- **FAIL [TAXONOMY]** `3_1/writhe_bad`
- **FAIL [TAXONOMY]** `3_1/core_bad`

## Mode ledger

| Knot | Mode | Family | Gap eV | Coupling | tau s | 3-gate active | Gap claim fail |
|---|---|---|---:|---:|---:|---|---|
| 3_1 | kelvin_bad | kelvin | 0.5 | 0.2 | 0.0001 | True | True |
| 3_1 | twist_bad | twist | 0.1 | 0.1 | 0.0001 | True | False |
| 3_1 | writhe_bad | writhe | 0.05 | 0.1 | 0.0001 | True | False |
| 3_1 | core_bad | core | 0.2 | 0.05 | 0.0001 | True | False |

## Thermodynamics

| Knot | Cv/kB | Limit | Status |
|---|---:|---:|---|
| 3_1 | 0.657035762 | 0.01 | FAIL |

## Spectroscopy

| Observable | Bound eV | Empirical limit eV | Status |
|---|---:|---:|---|
| line_fail | 0.005 | 0.0001 | FAIL |

## Canonical scale checks

- 0.5 rho_f v_swirl^2 = 418774.392 Pa
- v_swirl/r_c = 7.76344066e+20 s^-1
- These are scale checks only, not a knot-gas pressure or a mode gap.
