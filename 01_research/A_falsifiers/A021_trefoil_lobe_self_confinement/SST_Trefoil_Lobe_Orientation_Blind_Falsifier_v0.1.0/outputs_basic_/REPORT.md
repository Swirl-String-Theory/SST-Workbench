# SST Trefoil Lobe-Orientation Blind Falsifier

**Overall verdict:** `FAIL`

## Unblinded datasets

### B01 → knotplot_final
Status: **FAIL**

| Gate | Pass |
|---|---:|
| G0_numerical_sanity | True |
| G1_relative_equilibrium | True |
| G2_reduced_stability | False |
| G3_cross_lobe_stabilizes | False |
| G4_nearest_pair_cross_separates | True |
| G5_orientation_specificity | False |
| G6_ringdown_bounded | True |

### B02 → fremlin_fseries
Status: **FAIL**

| Gate | Pass |
|---|---:|
| G0_numerical_sanity | True |
| G1_relative_equilibrium | True |
| G2_reduced_stability | False |
| G3_cross_lobe_stabilizes | False |
| G4_nearest_pair_cross_separates | True |
| G5_orientation_specificity | False |
| G6_ringdown_bounded | True |

## Circle null controls
- B01: radial mean `0.000000e+00`, pass `True`
- B02: radial mean `0.000000e+00`, pass `True`

## Interpretation
`PASS` means both independent trefoil representations passed the preregistered critical gates. `FAIL` means at least one critical mechanism gate failed with numerically converged data. `INCONCLUSIVE` is used when numerical/core-clearance prerequisites fail.

No reconnection operator is present anywhere in this package; a near-core event is reported, not repaired or reconnected.