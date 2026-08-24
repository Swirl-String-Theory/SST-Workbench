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

## v0.3 research-track extensions from Boltzmann and Verlinde

| Research object | Code implementation | Status |
|---|---|---|
| Boltzmann complexion multiplicity `N!/prod w_i!` | `boltzmann.log_multinomial_complexions` | orthodox statistical-mechanics comparison |
| maximum-permutability equilibrium candidate | `boltzmann.maximum_permutability_audit` | conditional equilibrium gate |
| Boltzmann occupation law | `boltzmann.boltzmann_occupation_audit` | conditional equilibrium gate |
| microcanonical `1/T=dS/dE` | `boltzmann.microcanonical_temperature` | sampled-state diagnostic |
| `S=k_B ln N_accessible` versus position | `boltzmann.state_count_entropy_force` | sampled-state diagnostic |
| `F_ent=T dS/dx` vs SST pressure force | `verlinde.force_reference_audit` | speculative bridge falsifier |
| `grad(1/T) x grad p = 0` | `verlinde.integrability_audit` | new derived consistency condition |
| Verlinde entropy-displacement coefficient | `verlinde.entropy_displacement_audit` | optional external bridge |
| holographic area law/equipartition/inferred `G` | `verlinde.screen_audit` | optional external bridge |
| inverse-square radial slope | `verlinde.newton_power_law_audit` | comparison gate |
| entropy per bit vs Newton potential | `verlinde.potential_entropy_audit` | optional external bridge |
| `r_c^2/l_P^2` hierarchy | `verlinde.canonical_holographic_scale_check` | numerical guard only |

### Deliberately not canonized by v0.3

- gravity being fundamentally entropic;
- a holographic SST screen;
- one bit per SST core area;
- equipartition of unresolved SST microscopic degrees of freedom;
- Verlinde's relativistic Einstein-equation reconstruction as an SST derivation.

These appear only as explicitly switchable research claims.
