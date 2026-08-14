# Canon traceability

This package is designed against the research-track block **Maxwell–SST Kinetic Closure and Internal-Mode Thermodynamic Gate**.

| Research-track object | Code implementation |
|---|---|
| generalized mode families: translation/orientation/Kelvin/twist/writhe/core | `modes.csv`, `ledger.taxonomy_guard` |
| `omega > 0` does not imply `Delta > 0` | `gaps.classify_amplitude_scans` |
| true-gap / admissible-state guard | explicit `gap_status`; finite intercept is only a candidate threshold |
| direct coupling gate `G != 0` | declared `coupling_norm` or encounter-derived transfer proxy |
| three-gate condition: coupling, accessibility, equilibration | `coupling.three_gate` |
| internal partition function and `C_V` | `thermo.discrete_partition` |
| spectroscopic bound | `observables.spectroscopy_bound` |
| encounter energy-channel ledger | `ledger.energy_ledger_audit` |
| writhe is geometric unless independently dynamical | `taxonomy_guard` |
| kinetic knot stress `Pi_ij` | `observables.kinetic_stress` |
| ensemble isotropy `Q_ij -> 0` | `observables.orientation_Q` |
| resolution falsifier | `convergence.convergence_audit` |

## Deliberately not implemented as a derived SST result

- a Maxwellian knot distribution;
- a hard-sphere collision kernel;
- a numerical value of any SST internal-mode gap;
- an automatic identification of `omega` with `Delta/hbar`;
- an independent writhe oscillator;
- a core/twist spectrum when the underlying solver does not resolve a material frame and finite core.
