# A053 — Electron Topological Phase-Transition Tournament Blind Falsifier v0.1.0

## Research question

Can a single SST electron sector be distinguished between four preregistered topology/dynamics hypotheses under one common, blind interaction protocol?

| Model | Free propagation | Interaction / detection hypothesis |
|---|---|---|
| **H0** | `3_1` | remains `3_1` |
| **H1** | `L2a1` | remains `L2a1`; interaction may phase-lock internal modes only |
| **H2** | `L2a1` | topology-changing transition to `L4a1` |
| **H3** | `3_1` | transient multi-component `L2a1`/`L4a1`-like compound during interaction |

This is a **tournament falsifier**, not a topology assignment. No hypothesis is the default winner.

## Core scientific rule

The producer receives an interaction pulse and numerical tolerances, but **never a requested final topology**. `L2a1`, `L4a1`, or a compound state are classified only from output observables after the run.

For two components, the primary topological discriminator is the Gauss linking number

\[
\operatorname{Lk}(C_1,C_2)=\frac{1}{4\pi}\oint_{C_1}\oint_{C_2}
\frac{(\mathrm d\mathbf r_1\times\mathrm d\mathbf r_2)\cdot(\mathbf r_1-\mathbf r_2)}
{\|\mathbf r_1-\mathbf r_2\|^3}.
\]

The blind evaluator uses only the dimensionless topology/dynamics record. SST constants and the electron rest-energy are reveal-only.

## Important model-class boundary

A smooth ideal-Euler filament evolution preserves vortex-line topology. Therefore a producer declaring

```text
physics_class = ideal_euler_no_reconnection
```

**cannot physically realize H2 or H3 topology change**. The evaluator marks those hypotheses `MODEL_CLASS_FORBIDS_TRANSITION`, rather than interpreting absence of reconnection as evidence against all finite-core SST models.

H2/H3 require a separately declared finite-core/reconnection-capable producer. The reconnection algorithm must be local and target-blind.

## Fair circulation sectors

Links are run under both preregistered normalizations:

1. `per_component_quantum`: each component has \(|\Gamma_i|=1\) in blind units;
2. `fixed_total_equal_split`: \(|\Gamma_1|=|\Gamma_2|=1/2\), so total absolute circulation matches the single-component control.

For each, co- and counter-oriented sectors are retained. The tournament may not select whichever normalization helps one hypothesis after seeing results.

## Gates

A scientific model PASS requires its mandatory gates, including:

- input provenance and source independence;
- initial topology;
- free-propagation topology survival;
- sham-pulse control;
- numerical convergence;
- source/carrier robustness;
- energy/helicity accounting within the declared producer model;
- hypothesis-specific interaction gate;
- no target-aware topology surgery;
- post-interaction persistence or transient-return condition as applicable.

A diagnostic score is emitted for exploration but **never substitutes for mandatory gates**. Multiple hypotheses may survive, or all may fail.

## Workbench placement

```text
01_research/A_falsifiers/
  A053_electron_topological_phase_transition_tournament/
    FAMILY.yaml
    A053-v0.1.0/
```

A053 is a **candidate allocation** based on the Drive audit performed 2026-10-05: named A-falsifiers were found through A052; no named A053 family was found. Registry patches are additive candidates and must be checked against the local current registry before application.

## Upstream contracts

- **E010 PKLSA v0.3.1**: authoritative geometry/provenance qualification.
- **E011 SKLSA v0.2.0**: selected set already includes `3_1`, `L2a1`, and `L4a1`.
- **A051**: phase-locking observables and conservative status semantics.
- **A007 / ideal-link campaign**: existing `L2a1`/`L4a1` relative-equilibrium evidence.
- **E012/C006**: current dynamic-eigenmode bridge is trefoil-first; link-mode production remains an explicit blocker for fully symmetric H0--H3 modal comparison.

## Run

From this version directory:

```cmd
run_all.cmd C:\workspace\projects\SST-Workbench
```

This runs evaluator self-tests and, when a Workbench root exists, emits an upstream campaign plan. It does **not** fabricate missing physical trajectories.

Evaluate real producer output:

```cmd
python -m a053_etptf.cli evaluate --manifest path\to\manifest.json --output-dir outputs\physical
```

Generate only the local Workbench carrier plan:

```cmd
run_plan.cmd C:\workspace\projects\SST-Workbench
```

Reveal (after blind outputs are frozen):

```cmd
run_reveal.cmd outputs\physical\TOURNAMENT_SUMMARY.json private_reveal\reveal_config.json
```

## Output separation

The intended production convention is

```text
A053_Electron_Topological_Phase_Transition_Tournament_v0.1.0-outputs/
A053_Electron_Topological_Phase_Transition_Tournament_v0.1.0-outputs_BLIND.zip
A053_Electron_Topological_Phase_Transition_Tournament_v0.1.0-outputs_REVEALED.zip
```

Reveal never recomputes blind scientific observables.
