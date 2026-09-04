# 1_Maxwell_SST_Kinetic_Falsifier v0.3.0

Workbench **#1** for the SST research track **“Maxwell–SST Kinetic Closure and Internal-Mode Thermodynamic Gate.”**

v0.3.0 keeps the v0.2 centerline/C++ workflow and adds a strict **Boltzmann–Verlinde statistical closure layer**.  The new layer does not declare gravity entropic.  It tests whether an independently sampled SST microstate ensemble can support that bridge without replacing the Euler/pressure mechanism.

## Major additions in v0.3.0

### Boltzmann 1877 gates

- explicit distinction between microscopic complexions, occupation/state distributions, and coarse-grained macrostate observables;
- maximum-permutability test among candidate distributions at fixed `N` and total energy;
- stable combinatorial state counting
  `log P = log(N!/prod w_i!) + sum_i w_i log(g_i)`;
- measured occupation fit to `p_i propto g_i exp(-E_i/kBT)`;
- fitted temperature, `R^2`, and KL divergence against the preregistered temperature;
- optional detailed-balance gate for a claimed equilibrated sector;
- state-count entropy `S = k_B log N_accessible`;
- microcanonical temperature from `1/T = dS/dE`;
- entropy-gradient force `F_ent = T dS/dx` from held-out position-dependent state counts.

### Boltzmann–Verlinde–SST bridge gates

- blind comparison
  `F_ent = T dS/dx` versus an **independently computed** hydrodynamic force;
- SST pressure-force fallback
  `F_hyd = -(m/rho_f) dp/dx` when a direct force is not supplied;
- integrability gate for a scalar entropy potential:
  `grad(1/T) x grad(p) = 0`;
- Verlinde entropy-displacement postulate audit;
- holographic-screen area scaling `N propto A`;
- equipartition audit `E = (1/2) N k_B T`;
- inferred-`G` consistency from `N = A c^3/(G hbar)`;
- radial inverse-square slope gate;
- potential/entropy-per-bit relation audit;
- canonical hierarchy guard showing that `r_c^2/l_P^2` is enormous, so **one bit per SST core area is not silently assumed**.

### Preserved v0.2 functionality

- KnotPlot/Geomview `VECT`, XYZ/CSV/NPY import;
- uniform arclength resampling;
- length/curvature/RMS-radius/writhe geometry audit;
- rigid translation/global rotation removal;
- rigid-projected normal Fourier Kelvin/shape candidate basis;
- regularized centerline Biot–Savart encounter probes;
- translation/rotation/residual-shape decomposition;
- mode-projection proxy, writhe directional response, minimum separation;
- C++17/pybind11 acceleration with native-first dispatch and Python fallback;
- strict gap/thermodynamic/spectroscopic/energy-ledger/taxonomy gates.

## Interpretation boundary

The following are intentionally kept separate:

1. **centerline geometry/proxy layer** — does not derive an SST energy spectrum;
2. **physical Maxwell kinetic layer** — requires energies, gaps, relaxation times, couplings and empirical limits from a declared solver/experiment;
3. **Boltzmann state-counting layer** — requires actual sampled/derived accessible-state counts inside frozen invariant sectors;
4. **Verlinde bridge layer** — optional.  A failure rejects that bridge/closure, not automatically the underlying SST Euler dynamics.

A campaign reports `RESEARCH_CLOSURE_FAILURE` only when a corresponding entry in `research_claims` was preregistered `true`.

## Windows workspace

Expected location:

```text
C:\workspace\projects\SST-Workbench\SST_Maxwell\1_Maxwell_SST_Kinetic_Falsifier_v0.3.0
```

Default relaxed-knot directory in `config\paths.cmd`:

```text
C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

Shared environment preference:

```text
C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe
```

## Ready-made commands

### One-command safe default

```cmd
run_all.cmd
```

This performs install/tests, checks the backend, runs the basic relaxed-knot workflow, and runs both the expected-PASS and expected-FAIL Boltzmann/Verlinde synthetic audits.

### Geometry / coupling workbench

```cmd
run_00_install.cmd
run_01_check_backend.cmd
run_10_basic.cmd
run_20_extended.cmd
run_21_extended_unique_pairs.cmd
```

or:

```cmd
run_all_basic.cmd
run_all_extended.cmd
```

The extended workflow requires the C++ backend.

### Boltzmann/Verlinde self-tests

```cmd
run_40_bv_demo_pass.cmd
run_41_bv_demo_fail.cmd
```

or:

```cmd
run_all_boltzmann_verlinde.cmd
```

The FAIL demo is deliberately constructed to trip the preregistered research-closure gates.  A successful execution therefore still exits normally; inspect the generated report.

### Physical campaign

After `run_10_basic.cmd` or `run_20_extended.cmd`, use:

```text
outputs\basic\physical_campaign_skeleton\
```

or

```text
outputs\extended\physical_campaign_skeleton\
```

Populate only the tables supported by your declared physical solver/sampler.  Set a `research_claims` flag to `true` **only before opening held-out results**.

Then run:

```cmd
run_30_physical_falsifier.cmd ^
  outputs\extended\physical_campaign_skeleton\config.json ^
  outputs\physical_audit
```

`run_42_bv_physical.cmd` is an equivalent explicit alias for campaigns using the new statistical bridge tables.

## New v0.3 physical tables

- `state_distribution.csv` — combinatorial occupation bins for Boltzmann permutability;
- `state_occupations.csv` — energy-state occupations for the Boltzmann law fit;
- `state_counts.csv` — accessible-state count versus position and energy;
- `detailed_balance.csv` — optional transition-count equilibrium test;
- `force_reference.csv` — independently computed hydrodynamic/pressure force;
- `integrability.csv` — temperature- and pressure-gradient vectors;
- `screens.csv` — optional holographic-screen tests;
- `entropy_displacement.csv` — optional Verlinde entropy-gradient postulate;
- `radial_force.csv` — inverse-square scaling test;
- `potential_entropy.csv` — optional potential/entropy-per-bit relation.

See `docs\DATA_SCHEMA.md`, `docs\PREREGISTRATION.md`, and `docs\BOLTZMANN_VERLINDE_GATES.md`.

## C++ acceleration

The expensive `O(N^2)` centerline operations remain implemented in `cpp\native.cpp`:

- regularized Biot–Savart velocity;
- midpoint writhe diagnostic;
- inter-segment minimum distance;
- segment lengths.

The v0.3 statistical audits are `O(N)` or small regressions and do not need native acceleration.  Keeping them in Python also makes the statistical formulas easy to inspect and audit.

## Primary outputs

The centerline workflow writes:

```text
discovered_files.csv
geometry_metrics.csv
mode_candidates.csv
mode_family_capabilities.csv
interaction_coupling_proxy.csv
workflow_summary.json
README_RESULTS.md
resampled_unit_rms\*.csv
physical_campaign_skeleton\
```

A strict campaign writes:

```text
report.json
report.md
```

The JSON contains all per-gate numerical diagnostics, including closure failures that are summarized in Markdown.
