# Maxwell–SST falsifier report — bv_synthetic_pass

**Dataset:** `synthetic`  
**Verdict:** `DEMO_ONLY`

> Absence of a triggered falsifier is **not** validation of SST.

## Conditions

- T = 300 K
- kBT = 0.0258519998 eV
- observation time = 1 s
- drive energy = 0 eV

## Physical falsifiers

- None triggered by the supplied data.

## Research-closure failures

- None triggered for the preregistered optional Boltzmann/Verlinde claims.

## Numerical / closure failures

- None triggered by the supplied data.

## Mode ledger

| Knot | Mode | Family | Gap eV | Coupling | tau s | 3-gate active | Gap claim fail |
|---|---|---|---:|---:|---:|---|---|

## Thermodynamics

No declared discrete/gapped internal levels available for a partition-function audit.

## Boltzmann 1877 state-counting layer

- Permutability distributions: 2
- Maximum-permutability macrostate tests: 1
- Boltzmann occupation fits: 1
- Detailed-balance rows: 3
- Entropy-force derivative rows: 9
- Microcanonical-temperature estimates: 3

| Ensemble | Knot | T_fit K | rel T error | R2 | KL nats | Status |
|---|---|---:|---:|---:|---:|---|
| eq1 | 3_1 | 300 | 2.65269e-15 | 1 | 0 | PASS |

## Boltzmann–Verlinde–SST bridge

- Entropic-force vs independent pressure/hydrodynamic force comparisons: 9
- Pressure/temperature integrability checks: 1
- Holographic-screen series: 1
- Entropy-displacement postulate rows: 1
- Inverse-square radial series: 1
- Potential/entropy rows: 1

| Series | x m | F_ent N | F_hyd N | rel error | sign | Status |
|---|---:|---:|---:|---:|---|---|
| force1 | -1e-09 | 1e-12 | 1e-12 | 7.8356e-14 | True | PASS |
| force1 | 0 | 1e-12 | 1e-12 | 7.47209e-15 | True | PASS |
| force1 | 1e-09 | 1e-12 | 1e-12 | 1.42979e-13 | True | PASS |
| force1 | -1e-09 | 1e-12 | 1e-12 | 1.0986e-13 | True | PASS |
| force1 | 0 | 1e-12 | 1e-12 | 7.47209e-15 | True | PASS |
| force1 | 1e-09 | 1e-12 | 1e-12 | 1.42979e-13 | True | PASS |
| force1 | -1e-09 | 1e-12 | 1e-12 | 1.41566e-13 | True | PASS |
| force1 | 0 | 1e-12 | 1e-12 | 7.47209e-15 | True | PASS |
| force1 | 1e-09 | 1e-12 | 1e-12 | 1.63578e-14 | True | PASS |

## Spectroscopy

No spectroscopy rows supplied.

## Canonical scale checks

- 0.5 rho_f v_swirl^2 = 418774.392 Pa
- v_swirl/r_c = 7.76344066e+20 s^-1
- (r_c/l_P)^2 = 7.59947904e+39
- G from one holographic bit per r_c^2 = 5.07212029e+29 m^3 kg^-1 s^-2
- The holographic quantities are hierarchy diagnostics only; they are not canonized SST identifications.
