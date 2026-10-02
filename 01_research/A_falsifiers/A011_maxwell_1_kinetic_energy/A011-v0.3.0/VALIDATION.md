# Validation — 1_Maxwell_SST_Kinetic_Falsifier v0.3.0

Validation date: 2026-08-19.

## Python test suite

```text
24 passed, 1 skipped
```

The skipped test is the conditional C++/Python numerical-parity test because `pybind11` is not installed in the artifact execution sandbox. The native source/build path is unchanged in architecture and runs automatically when the target Windows Workbench has `pybind11`/MSVC available.

Covered by tests:

- legacy campaign/gap/coupling/thermodynamic/taxonomy behavior;
- VECT import and closed-curve arclength resampling;
- rigid translation decomposition;
- rigid-projected Kelvin/shape candidate generation;
- Python fallback midpoint writhe and regularized Biot–Savart checks;
- exact multinomial complexion counting (`7!/(4!2!1!) = 105` regression);
- Boltzmann-law fit recovering a known 300 K synthetic distribution;
- entropy-gradient force recovery from analytic `log N(E,x)`;
- microcanonical `dS/dE` temperature recovery;
- Verlinde entropy-displacement coefficient;
- pressure/temperature integrability pass/fail controls;
- holographic area-law + equipartition + inferred-`G` synthetic control;
- inverse-square force-slope control;
- full v0.3 synthetic PASS and deliberately falsified FAIL campaigns.

## v0.3 Boltzmann/Verlinde synthetic campaigns

Both datasets are explicitly `dataset_kind=synthetic`, therefore the top-level verdict remains `DEMO_ONLY`.

### Expected PASS

`examples/bv_synthetic_pass/`

- maximum-permutability equilibrium candidate: PASS;
- Boltzmann occupation fit: PASS (`T_fit = 300 K` within numerical precision);
- detailed balance: PASS;
- `F_ent = T dS/dx` vs independent force: PASS;
- integrability: PASS;
- entropy-displacement: PASS;
- area law / inferred `G` / equipartition: PASS;
- inverse-square slope: PASS;
- potential/entropy-per-bit relation: PASS.

### Expected FAIL

`examples/bv_synthetic_fail/` intentionally breaks the same assumptions and triggers multiple `research_closure_failures`, including:

- `MAXIMUM_PERMUTABILITY`;
- `BOLTZMANN_EQUILIBRIUM`;
- `DETAILED_BALANCE`;
- `ENTROPIC_PRESSURE_FORCE`;
- `PRESSURE_ENTROPY_INTEGRABILITY`;
- `VERLINDE_ENTROPY_DISPLACEMENT`;
- `VERLINDE_SCREEN`;
- `NEWTON_INVERSE_SQUARE`;
- `VERLINDE_POTENTIAL_ENTROPY`.

## Solver-facing smoke workflow

Input: the two bundled synthetic closed VECT curves.

Basic preset result in the sandbox:

```text
files_discovered      = 2
curves_parsed         = 2
parse_failures        = 0
resample_n            = 300
max_fourier_m         = 6
mode_candidates       = 48
interaction_probes    = 2
backend                = python fallback
```

The generated `physical_campaign_skeleton/` contains all legacy physical tables plus the new state-count, force-reference, integrability and screen tables.

## C++ backend status

`pybind11` is not installed in the execution sandbox, so native compilation was not attempted here. On the target Windows Workbench:

```cmd
run_00_install.cmd
run_01_check_backend.cmd
```

installs/builds the native backend and reports the active implementation. `run_20_extended.cmd` still requires C++ explicitly.

## Interpretation audit

No centerline geometry proxy is promoted into `gap_eV`, a physical mode energy, an accessible-state count, or an entropy.  The v0.3 Boltzmann/Verlinde layer accepts only externally generated physical/sampling tables.  Optional bridge assumptions only become pass/fail claims when explicitly enabled in `research_claims` before held-out inspection.
