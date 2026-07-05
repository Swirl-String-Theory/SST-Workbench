# SST chi-phase package v13B.0

**Track:** unified A/B `alpha_ring` benchmark pipeline  
**Status:** Strong Research Track synthesis; not locked CANON

## Purpose

v13B.0 consolidates the two active ring-constant routes:

- **Track A:** incompressible Euler / Biot--Savart vorticity-energy extraction.
- **Track B:** GP/NLSE core-envelope energy with the corrected depletion coefficient and algebraic tail correction.

The goal is not to introduce a new derivation, but to place both tracks in one auditable table so the selector split is explicit.

## Core result

The unified comparison gives:

$$ 
\alpha_{\rm ring}^{A}[\text{smooth }a_0^\star]\approx 1.504718,
 $$ 

while

$$ 
\alpha_{\rm ring}^{B}[\text{GP/NLSE},\infty]\approx 1.619350923.
 $$ 

Thus the v6 chi-closure profile and the GP/NLSE ring-energy constant are not the same selector. This is the important v13B.0 result.

## Principal status

$$ 
\boxed{\text{Track A smooth chi-closure does not reproduce the NLS ring constant.}}
 $$ 

$$ 
\boxed{\text{Track B GP/NLSE does reproduce a value close to legacy NLS }1.61.}
 $$ 

$$ 
\boxed{\text{Locked CANON still requires the SST-internal proof }A_{\rm grad}=B_{\rm phase}=C_{\rm depletion}.}
 $$ 

## Files

- `simulate_chi_phase_v13B0.py` — command-line runner.
- `sst_chi_phase_v13B0_py.py` — benchmark data model and synthesis logic.
- `DERIVATION_UNIFIED_TRACK_AB.md` — technical derivation/interpretation notes.
- `CANON_STATUS.md` — canon gates and labels.
- `MANIFEST.md` — file manifest.
- `provenance/` — copied summaries from v10A.0, v10B.1, v11B.0, and v12B.0.
- `exports/` — generated CSVs, plots, and summary.

## Run

```bash
python simulate_chi_phase_v13B0.py
```

Without plots:

```bash
python simulate_chi_phase_v13B0.py --no-plots
```

## Outputs

- `exports/chi_v13B0_unified_benchmark.csv`
- `exports/chi_v13B0_summary_metrics.csv`
- `exports/chi_v13B0_canon_gates.csv`
- `exports/chi_v13B0_unified_alpha_benchmark.png`
- `exports/chi_v13B0_delta_legacy_nls.png`
- `exports/chi_v13B0_selector_split.png`
- `exports/chi_v13B0_run_results_summary.txt`

## Canon warning

Use `alpha_ring` and `beta_ring`, not bare `alpha` and `beta`. In SST canon, bare `alpha` is easily confused with the fine-structure/shielding-gate constant, and `alpha'` is orthodox string-theory Regge slope notation. This package is specifically about vortex-ring constants.