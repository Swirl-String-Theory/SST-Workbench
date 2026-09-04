# SST Trefoil Coupled Torsion–Breathing–Kelvin + RPO/Floquet Falsifier v0.3.0

**Overall verdict:** `FAIL`

## Unblinded datasets

### B01 → knotplot_final
Status: **FAIL**

| Gate | Role | Pass |
|---|---|---:|
| G0_numerical_sanity | critical | True |
| G1_relative_equilibrium | diagnostic | True |
| G2_reduced_stability | critical | False |
| G3_cross_lobe_stabilizes | critical | False |
| G4_nearest_pair_cross_separates | critical | True |
| G5_orientation_specificity | diagnostic | False |
| G6_ringdown_bounded | critical | True |
| G7_matched_orientation_specificity | diagnostic | False |
| G8_cross_repulsion_coherent | diagnostic | False |
| G9_dominant_mode_cross_stabilizes | diagnostic | False |
| G10_C3_sector_localized | diagnostic | False |
| G11_counterfactual_causal_consistency | diagnostic | True |
| G12_TBK_mode_resolved | diagnostic | True |
| G13_torsion_coupling_stabilizes | diagnostic | False |
| G14_kelvin_coupling_stabilizes | diagnostic | False |
| G15_breathing_coupling_stabilizes | diagnostic | False |
| G16_TBK_collective_coupling_stabilizes | diagnostic | False |
| G17_TBK_phase_lock | diagnostic | False |
| G18_RPO_recurrence | diagnostic | False |
| G19_Floquet_bounded | diagnostic | False |

Dominant reduced eigenvalue: `0.260105 -0.19655i`
Dominant sector: `m0`; cross-lobe real contribution: `0.124252`.
TBK expanded basis: `21` modes; RPO best recurrence: `n/a`; phase-lock strength: `n/a`; Floquet radius excl. neutral: `n/a`.

### B02 → fremlin_fseries
Status: **FAIL**

| Gate | Role | Pass |
|---|---|---:|
| G0_numerical_sanity | critical | True |
| G1_relative_equilibrium | diagnostic | True |
| G2_reduced_stability | critical | False |
| G3_cross_lobe_stabilizes | critical | False |
| G4_nearest_pair_cross_separates | critical | True |
| G5_orientation_specificity | diagnostic | False |
| G6_ringdown_bounded | critical | True |
| G7_matched_orientation_specificity | diagnostic | False |
| G8_cross_repulsion_coherent | diagnostic | False |
| G9_dominant_mode_cross_stabilizes | diagnostic | False |
| G10_C3_sector_localized | diagnostic | False |
| G11_counterfactual_causal_consistency | diagnostic | True |
| G12_TBK_mode_resolved | diagnostic | True |
| G13_torsion_coupling_stabilizes | diagnostic | False |
| G14_kelvin_coupling_stabilizes | diagnostic | False |
| G15_breathing_coupling_stabilizes | diagnostic | False |
| G16_TBK_collective_coupling_stabilizes | diagnostic | False |
| G17_TBK_phase_lock | diagnostic | False |
| G18_RPO_recurrence | diagnostic | False |
| G19_Floquet_bounded | diagnostic | False |

Dominant reduced eigenvalue: `0.260221 -0.127763i`
Dominant sector: `m0`; cross-lobe real contribution: `0.0499104`.
TBK expanded basis: `21` modes; RPO best recurrence: `n/a`; phase-lock strength: `n/a`; Floquet radius excl. neutral: `n/a`.

## Circle null controls
- B01: radial mean `0.000000e+00`, pass `True`
- B02: radial mean `0.000000e+00`, pass `True`

## Interpretation
`PASS` for the overall campaign still uses the immutable v0.1 critical set G0/G2/G3/G4/G6. v0.2 diagnostics G7–G11 remain unchanged; v0.3 adds G12–G19 for coupled torsion/breathing/Kelvin causality, phase locking, RPO recurrence and conditional Floquet stability without moving the original goalposts.

No reconnection, hard-core bounce, cut/splice, or penalty-force operator is present. Near-core events are reported only.

See `GATE_CONCLUSIONS.md` for every gate. v0.3 additionally writes `coupled_spectrum.csv`, `family_coupling_ablation.csv`, `phase_lock.csv`, `rpo_phase_scan.csv`, and `floquet_multipliers.csv`.