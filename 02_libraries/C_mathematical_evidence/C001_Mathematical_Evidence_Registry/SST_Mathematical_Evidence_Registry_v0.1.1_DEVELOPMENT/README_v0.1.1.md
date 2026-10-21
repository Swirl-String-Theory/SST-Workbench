# SST Mathematical Evidence Registry v0.1.1

**Status:** DEVELOPMENT / NOT PHYSICALLY CERTIFIED · 21 October 2026.

This release is an *addendum* to the complete v0.1.0 evidence registry. The original source files and source hashes, the 379 unreviewed raw formula candidates and all 41 previous curated claims are **preserved unchanged**. No old score or interpretation is automatically promoted to evidence.

## Added mathematical content

1. **Kelvin-wave mathematics.** Correct slim-filament asymptotic dispersion, periodic wavenumber diagnostic, two incompatible circulation input contracts, independent energy conversion, and dimensional repair flags for gap and tension formulae. This is NOT a certified knotted-vortex eigenvalue solution.
2. **Conditional Bose thermodynamics.** Stable single-oscillator partition function, energy and heat capacity, exact finite-`N` energy upper bound, thermal grid in SI units. A topological energy gap is **not** derived.
3. **Independent conservative 2-mode action.** Positive Hamiltonian, coupled normal modes, energy drift and second-order symplectic time convergence. Two generic mechanical degrees of freedom are not identified with photon or Swirl fields.
4. **Separate phenomenological energy-rate dynamics.** Dimensional repair of mixing rates, three-sector energy ledger (source, receiver, loss), analytic time-to-peak, and explicit 30 ns no-go for the two-rate parameter example.
5. **Source and verdict traceability.** 22 mathematical addendum entries (A001–A022), each with primary-paper locator, source statement, derived correction, scope, dimension and corresponding gate.

## Contents

- `Mathematical_Addendum_v0.1.1.pdf` — scientific audit, equations, plots, limits and test gates.
- `Mathematical_Addendum_v0.1.1.tex` — editable LaTeX source (ordinary LaTeX, no local macros needed beyond those defined at top).
- `results/mathematical_addendum.json` / `.csv` — 22 source-specific entries.
- `results/independent_numeric_checks.json` — test values, units and provenance warnings.
- `results/{kelvin_periodic_proxy,conditional_thermal_grid,two_sector_energy_rate_example,conservative_oscillator_energy_trace}.csv` — independent numeric diagnostics.
- `results/addendum_qualification.json` — explicit PASS and unresolved claims.
- `addendum/math_models.py` — pure mathematical model implementations (Python standard library).
- `addendum/build_addendum.py` — regenerate numeric output deterministically.
- `addendum/make_figures.py` — optional figure regeneration (requires matplotlib & numpy).
- `figures/` — mathematical diagnostic figures. Not experimental results.
- `build_registry.py`, `query_registry.py`, `tests/`, `sources/` — complete legacy registry preserved.

## Reproduce

Windows:

```bat
run_all.cmd
```

Linux/macOS:

```bash
bash run_all.sh
```

A successful run currently reports **55/55 Python regression tests (23 prior + 32 new)**. It is a numerical and algebraic software check, *not* evidence of actual stable PKLSA vortices or particle/vacuum physics.

To search all audited claims including the addendum:

```bash
python query_registry.py --source all Kelvin
python query_registry.py --source addendum --status DIMENSIONALLY_INVALID
python query_registry.py --source curated --paper SST-29
```

## Source-native data blocker

The actual current PKLSA engine and core model, frozen backend provenance, and native linear/Floquet-mode operator were not available in this release. The next version can test true eigenfrequencies only after provider validation, neutral-mode removal, spatial/temporal convergence and an independently calibrated vortex-circulation contract. A nonzero classical eigenfrequency is not yet a quantum energy gap.

**Proposed Workbench path:** `02_libraries/C_mathematical_evidence/SST_Mathematical_Evidence_Registry/SST_Mathematical_Evidence_Registry_v0.1.1/`.

**Do not interpret the numerical examples as a measured photon speed, electron mass, Kelvin gap, Unruh-echo delay or physical evidence for two interacting vacua.**
