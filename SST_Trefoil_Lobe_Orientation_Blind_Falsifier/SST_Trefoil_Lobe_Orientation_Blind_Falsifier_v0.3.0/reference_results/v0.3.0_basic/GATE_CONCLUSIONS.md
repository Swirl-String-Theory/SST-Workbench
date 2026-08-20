# Gate-by-gate conclusions

Campaign verdict: **FAIL**

Each conclusion below is generated from the preregistered thresholds and the blind score. Critical versus diagnostic status is explicit so later versions can be compared without silently changing the v0.1 decision rule.

## B01 → knotplot_final
Dataset status: **FAIL**

### G0_numerical_sanity — Numerical sanity / core clearance
**Role:** `critical`  
**Verdict:** `PASS`  
**Question:** Is the velocity split numerically closed and is the resolved finite core geometrically admissible?

**Conclusion:** The decomposition and core-clearance prerequisites are numerically admissible.

**Evidence**
- `split_closure_rel` = `5.13194e-16`
- `core_clearance_radii` = `1.11111`

**Criterion**
- `split_closure_max` = `1e-10`
- `min_thickness_over_core` = `1.05`

### G1_relative_equilibrium — Relative-equilibrium proximity
**Role:** `diagnostic`  
**Verdict:** `PASS`  
**Question:** After removing rigid translation/rotation and tangential motion, is intrinsic shape velocity small?

**Conclusion:** The seed is reasonably close to a relative-equilibrium-like state under this metric.

**Evidence**
- `shape_velocity_ratio` = `0.322177`

**Criterion**
- `base_shape_ratio_max` = `0.35`

### G2_reduced_stability — Reduced six-mode stability
**Role:** `critical`  
**Verdict:** `FAIL`  
**Question:** Are the six tilt/breathing perturbations linearly bounded within the preregistered growth and convergence limits?

**Conclusion:** At least one resolved reduced mode grows too strongly; the tested trefoil is not linearly stable in this subspace.

**Evidence**
- `normalized_growth` = `0.797829`
- `jacobian_convergence` = `0.00565119`

**Criterion**
- `normalized_growth_max` = `0.12`
- `jacobian_convergence_max` = `0.35`

### G3_cross_lobe_stabilizes — Global cross-lobe stabilization
**Role:** `critical`  
**Verdict:** `FAIL`  
**Question:** Does the cross-lobe Jacobian materially reduce the worst reduced growth rate?

**Conclusion:** Cross-lobe induction does not lower the worst reduced growth rate enough; local separation alone is not sufficient global stabilization.

**Evidence**
- `cross_jacobian_fraction` = `0.816225`
- `cross_growth_improvement` = `-0.535021`

**Criterion**
- `cross_jacobian_fraction_min` = `0.1`
- `cross_growth_improvement_min` = `0.02`

### G4_nearest_pair_cross_separates — Nearest-pair cross-lobe separation
**Role:** `critical`  
**Verdict:** `PASS`  
**Question:** At the closest cross-lobe approach, does cross-lobe induction increase separation?

**Conclusion:** The closest cross-lobe pair has the predicted separating induced velocity.

**Evidence**
- `nearest_pair_cross_rate` = `0.0256426`

**Criterion**
- `cross_pair_rate_min` = `0`

### G5_orientation_specificity — Legacy orientation specificity
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Do the original v0.1-style orientation scrambles grow more strongly than the seed?

**Conclusion:** The seed orientation is not uniquely favored over the legacy scramble controls.

**Evidence**
- `control_growth_delta` = `-0.0615024`
- `control_count` = `6`

**Criterion**
- `control_growth_delta_min` = `0.02`

### G6_ringdown_bounded — Finite-amplitude ringdown boundedness
**Role:** `critical`  
**Verdict:** `PASS`  
**Question:** Does the preregistered nonlinear tilt perturbation remain bounded without a core event?

**Conclusion:** The finite-amplitude perturbation remains bounded over the tested window without reconnection logic.

**Evidence**
- `max_over_initial` = `1`
- `core_event` = `n/a`

**Criterion**
- `ringdown_max_over_initial` = `1.75`
- `core_event_required_absent` = `True`

### G7_matched_orientation_specificity — Curvature-matched orientation specificity
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Among controls with closely matched curvature signatures, is the seed more stable?

**Conclusion:** After curvature matching, orientation alone is not shown to confer the preregistered stability advantage.

**Evidence**
- `matched_control_count` = `6`
- `matched_control_growth_delta` = `-0.0615024`
- `curvature_match_tolerance` = `0.12`

**Criterion**
- `matched_control_min_count` = `2`
- `matched_control_growth_delta_min` = `0.02`

### G8_cross_repulsion_coherent — Cross-lobe repulsion coherence
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Is separating cross-lobe motion coherent across multiple distinct close contacts and at lobe-centroid scale?

**Conclusion:** Separating motion is not coherent enough across distinct contacts/lobe pairs to support a global repulsion picture.

**Evidence**
- `contact_positive_fraction` = `0.583333`
- `contact_median_cross_rate` = `0.0169422`
- `lobe_pair_positive_fraction` = `0.666667`
- `angle_rate_correlation` = `0.162369`

**Criterion**
- `contact_repulsion_fraction_min` = `0.6`
- `contact_repulsion_median_min` = `0`
- `lobe_pair_repulsion_fraction_min` = `0.666667`

### G9_dominant_mode_cross_stabilizes — Dominant-mode causal attribution
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** In the biorthogonal eigenvalue decomposition of the most unstable mode, is the cross-lobe contribution stabilizing?

**Conclusion:** Cross-lobe coupling does not contribute a sufficiently negative real growth component to the dominant mode; it may be neutral or destabilizing.

**Evidence**
- `dominant_eigenvalue` = `{re: 0.260105, im: -0.19655}`
- `cross_real_contribution` = `0.124252`
- `cross_real_normalized` = `0.381122`
- `all_component_contributions` = `{local: {re: 0.00330425, im: -0.00559871}, same_lobe: {re: 0.118817, im: -0.342889}, cross_lobe: {re: 0.124252, im: 0.150361}, transition: {re: 0.0137323, im: 0.00157658}}`

**Criterion**
- `cross_real_normalized_max` = `-0.02`

### G10_C3_sector_localized — C3 symmetry-sector localization
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Is the dominant mode concentrated in a symmetry-adapted sector with limited m=0/E block leakage?

**Conclusion:** The dominant instability is strongly mixed across the reduced C3 sectors, so a single-lobe-mode explanation is inadequate.

**Evidence**
- `dominant_sector` = `m0`
- `sector_participation` = `{m0: 0.769822, E_tilt: 0.066067, E_breathe: 0.164111, E_total: 0.230178, tilt_total: 0.835873, breathe_total: 0.164127}`
- `sector_peak` = `0.769822`
- `block_leakage` = `0.77884`

**Criterion**
- `c3_sector_participation_min` = `0.55`
- `c3_block_leakage_max` = `0.45`

### G11_counterfactual_causal_consistency — Linear/nonlinear cross-lobe causality consistency
**Role:** `diagnostic`  
**Verdict:** `PASS`  
**Question:** Does short nonlinear evolution with and without cross-lobe induction order growth in the direction predicted by modal attribution?

**Conclusion:** The counterfactual nonlinear ordering agrees with the linear cross-lobe causal sign.

**Evidence**
- `linear_cross_real_contribution` = `0.124252`
- `full_early_log_growth` = `0.322397`
- `without_cross_early_log_growth` = `0.0421926`
- `nonlinear_full_minus_without_cross_growth` = `0.280204`
- `full_core_event` = `n/a`
- `without_cross_core_event` = `n/a`

**Criterion**
- `same_sign_required` = `True`
- `minimum_absolute_growth_difference` = `0.0001`

### G12_TBK_mode_resolved — Coupled torsion–breathing–Kelvin mode resolved
**Role:** `diagnostic`  
**Verdict:** `PASS`  
**Question:** Does the selected oscillatory reduced mode contain non-negligible breathing, torsion and Kelvin participation simultaneously?

**Conclusion:** A genuinely mixed torsion–breathing–Kelvin oscillatory mode is resolved in the expanded basis.

**Evidence**
- `selected_eigenvalue` = `{re: -7.77187e-05, im: 0.483775}`
- `family_participation` = `{tilt: 0.124791, breathing: 0.0642755, torsion: 0.65179, kelvin: 0.159144}`
- `minimum_TBK_participation` = `0.0642755`
- `coupled_jacobian_convergence` = `0.0218286`

**Criterion**
- `coupled_family_participation_min` = `0.02`
- `coupled_jacobian_convergence_max` = `0.3`

### G13_torsion_coupling_stabilizes — Torsion-coupling stabilization
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Does removing off-diagonal torsion coupling increase the worst coupled-mode growth rate?

**Conclusion:** Torsion coupling is not shown to provide the preregistered stabilizing growth reduction.

**Evidence**
- `growth_penalty_when_torsion_decoupled` = `-0.115836`

**Criterion**
- `family_coupling_stabilization_min` = `0.01`

### G14_kelvin_coupling_stabilizes — Kelvin-coupling stabilization
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Does removing off-diagonal Kelvin coupling increase the worst coupled-mode growth rate?

**Conclusion:** Kelvin coupling is not shown to provide the preregistered stabilizing growth reduction.

**Evidence**
- `growth_penalty_when_kelvin_decoupled` = `-0.122357`

**Criterion**
- `family_coupling_stabilization_min` = `0.01`

### G15_breathing_coupling_stabilizes — Breathing-coupling stabilization
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Does removing off-diagonal breathing coupling increase the worst coupled-mode growth rate?

**Conclusion:** Breathing coupling is not shown to provide the preregistered stabilizing growth reduction.

**Evidence**
- `growth_penalty_when_breathing_decoupled` = `-0.026917`

**Criterion**
- `family_coupling_stabilization_min` = `0.01`

### G16_TBK_collective_coupling_stabilizes — Collective TBK coupling stabilization
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Does block-diagonalizing all mode families increase the worst growth rate relative to the fully coupled system?

**Conclusion:** The fully coupled TBK system is not more stable than the family-block-diagonal counterfactual by the preregistered margin.

**Evidence**
- `growth_penalty_when_all_families_block_diagonalized` = `-0.122357`

**Criterion**
- `collective_coupling_stabilization_min` = `0.02`

### G17_TBK_phase_lock — Torsion–breathing–Kelvin phase locking
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Along the best recurrence trajectory, do dominant breathing, torsion and Kelvin coordinates frequency-lock with stable relative phase?

**Conclusion:** No sufficiently coherent torsion–breathing–Kelvin phase lock is resolved over the tested trajectory.

**Evidence**
- `phase_lock_valid` = `False`
- `phase_lock_strength` = `nan`
- `relative_frequency_spread` = `nan`
- `pair_phase_locks` = `n/a`

**Criterion**
- `phase_lock_strength_min` = `0.65`
- `phase_frequency_spread_max` = `0.25`

### G18_RPO_recurrence — Relative-periodic-orbit recurrence
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** After removing rigid motion, does a phase-scanned coupled perturbation return sufficiently close to its initial shape without a near-core event?

**Conclusion:** No tested phase returns close enough to establish an RPO candidate under the preregistered threshold.

**Evidence**
- `excursion_reached` = `False`
- `peak_before_return` = `n/a`
- `return_ratio` = `n/a`
- `best_recurrence` = `nan`
- `best_period_steps` = `n/a`
- `best_period_time` = `n/a`
- `core_event` = `n/a`

**Criterion**
- `rpo_excursion_min` = `0.01`
- `rpo_recurrence_max` = `0.05`
- `rpo_return_ratio_max` = `0.65`
- `core_event_required_absent` = `True`

### G19_Floquet_bounded — Nonlinear return-map Floquet boundedness
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Conditional on a passing RPO recurrence, are the finite-difference return-map multipliers bounded after excluding one neutral multiplier nearest unity?

**Conclusion:** No valid RPO-conditioned Floquet test is available, or at least one tested non-neutral multiplier exceeds the preregistered bound.

**Evidence**
- `floquet_valid` = `False`
- `reason` = `no_rpo_candidate`
- `spectral_radius_excluding_neutral` = `nan`
- `period_steps` = `n/a`
- `period_time` = `n/a`

**Criterion**
- `floquet_requires_RPO_recurrence` = `True`
- `floquet_spectral_radius_max` = `1.05`

### Orientation/contact synthesis
- Distinct close-contact cross-lobe separating fraction: `0.583333`.
- Median cross-lobe separation rate across those contacts: `0.0169422`.
- Correlation of separation rate with antiparallelness: `0.162369`.
- Lobe-centroid pair separating fraction: `0.666667`.

## B02 → fremlin_fseries
Dataset status: **FAIL**

### G0_numerical_sanity — Numerical sanity / core clearance
**Role:** `critical`  
**Verdict:** `PASS`  
**Question:** Is the velocity split numerically closed and is the resolved finite core geometrically admissible?

**Conclusion:** The decomposition and core-clearance prerequisites are numerically admissible.

**Evidence**
- `split_closure_rel` = `6.2272e-16`
- `core_clearance_radii` = `1.11111`

**Criterion**
- `split_closure_max` = `1e-10`
- `min_thickness_over_core` = `1.05`

### G1_relative_equilibrium — Relative-equilibrium proximity
**Role:** `diagnostic`  
**Verdict:** `PASS`  
**Question:** After removing rigid translation/rotation and tangential motion, is intrinsic shape velocity small?

**Conclusion:** The seed is reasonably close to a relative-equilibrium-like state under this metric.

**Evidence**
- `shape_velocity_ratio` = `0.34296`

**Criterion**
- `base_shape_ratio_max` = `0.35`

### G2_reduced_stability — Reduced six-mode stability
**Role:** `critical`  
**Verdict:** `FAIL`  
**Question:** Are the six tilt/breathing perturbations linearly bounded within the preregistered growth and convergence limits?

**Conclusion:** At least one resolved reduced mode grows too strongly; the tested trefoil is not linearly stable in this subspace.

**Evidence**
- `normalized_growth` = `0.888025`
- `jacobian_convergence` = `0.00475917`

**Criterion**
- `normalized_growth_max` = `0.12`
- `jacobian_convergence_max` = `0.35`

### G3_cross_lobe_stabilizes — Global cross-lobe stabilization
**Role:** `critical`  
**Verdict:** `FAIL`  
**Question:** Does the cross-lobe Jacobian materially reduce the worst reduced growth rate?

**Conclusion:** Cross-lobe induction does not lower the worst reduced growth rate enough; local separation alone is not sufficient global stabilization.

**Evidence**
- `cross_jacobian_fraction` = `0.981185`
- `cross_growth_improvement` = `-0.431941`

**Criterion**
- `cross_jacobian_fraction_min` = `0.1`
- `cross_growth_improvement_min` = `0.02`

### G4_nearest_pair_cross_separates — Nearest-pair cross-lobe separation
**Role:** `critical`  
**Verdict:** `PASS`  
**Question:** At the closest cross-lobe approach, does cross-lobe induction increase separation?

**Conclusion:** The closest cross-lobe pair has the predicted separating induced velocity.

**Evidence**
- `nearest_pair_cross_rate` = `0.116994`

**Criterion**
- `cross_pair_rate_min` = `0`

### G5_orientation_specificity — Legacy orientation specificity
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Do the original v0.1-style orientation scrambles grow more strongly than the seed?

**Conclusion:** The seed orientation is not uniquely favored over the legacy scramble controls.

**Evidence**
- `control_growth_delta` = `-0.0490769`
- `control_count` = `6`

**Criterion**
- `control_growth_delta_min` = `0.02`

### G6_ringdown_bounded — Finite-amplitude ringdown boundedness
**Role:** `critical`  
**Verdict:** `PASS`  
**Question:** Does the preregistered nonlinear tilt perturbation remain bounded without a core event?

**Conclusion:** The finite-amplitude perturbation remains bounded over the tested window without reconnection logic.

**Evidence**
- `max_over_initial` = `1`
- `core_event` = `n/a`

**Criterion**
- `ringdown_max_over_initial` = `1.75`
- `core_event_required_absent` = `True`

### G7_matched_orientation_specificity — Curvature-matched orientation specificity
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Among controls with closely matched curvature signatures, is the seed more stable?

**Conclusion:** After curvature matching, orientation alone is not shown to confer the preregistered stability advantage.

**Evidence**
- `matched_control_count` = `6`
- `matched_control_growth_delta` = `-0.0490769`
- `curvature_match_tolerance` = `0.12`

**Criterion**
- `matched_control_min_count` = `2`
- `matched_control_growth_delta_min` = `0.02`

### G8_cross_repulsion_coherent — Cross-lobe repulsion coherence
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Is separating cross-lobe motion coherent across multiple distinct close contacts and at lobe-centroid scale?

**Conclusion:** Separating motion is not coherent enough across distinct contacts/lobe pairs to support a global repulsion picture.

**Evidence**
- `contact_positive_fraction` = `0.583333`
- `contact_median_cross_rate` = `0.0701965`
- `lobe_pair_positive_fraction` = `0.333333`
- `angle_rate_correlation` = `0.0374554`

**Criterion**
- `contact_repulsion_fraction_min` = `0.6`
- `contact_repulsion_median_min` = `0`
- `lobe_pair_repulsion_fraction_min` = `0.666667`

### G9_dominant_mode_cross_stabilizes — Dominant-mode causal attribution
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** In the biorthogonal eigenvalue decomposition of the most unstable mode, is the cross-lobe contribution stabilizing?

**Conclusion:** Cross-lobe coupling does not contribute a sufficiently negative real growth component to the dominant mode; it may be neutral or destabilizing.

**Evidence**
- `dominant_eigenvalue` = `{re: 0.260221, im: -0.127763}`
- `cross_real_contribution` = `0.0499104`
- `cross_real_normalized` = `0.170324`
- `all_component_contributions` = `{local: {re: 0.00113473, im: -0.0033238}, same_lobe: {re: 0.205359, im: -0.291425}, cross_lobe: {re: 0.0499104, im: 0.164848}, transition: {re: 0.00381704, im: 0.00213746}}`

**Criterion**
- `cross_real_normalized_max` = `-0.02`

### G10_C3_sector_localized — C3 symmetry-sector localization
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Is the dominant mode concentrated in a symmetry-adapted sector with limited m=0/E block leakage?

**Conclusion:** The dominant instability is strongly mixed across the reduced C3 sectors, so a single-lobe-mode explanation is inadequate.

**Evidence**
- `dominant_sector` = `m0`
- `sector_participation` = `{m0: 0.870024, E_tilt: 0.0352444, E_breathe: 0.0947314, E_total: 0.129976, tilt_total: 0.880152, breathe_total: 0.119848}`
- `sector_peak` = `0.870024`
- `block_leakage` = `0.859665`

**Criterion**
- `c3_sector_participation_min` = `0.55`
- `c3_block_leakage_max` = `0.45`

### G11_counterfactual_causal_consistency — Linear/nonlinear cross-lobe causality consistency
**Role:** `diagnostic`  
**Verdict:** `PASS`  
**Question:** Does short nonlinear evolution with and without cross-lobe induction order growth in the direction predicted by modal attribution?

**Conclusion:** The counterfactual nonlinear ordering agrees with the linear cross-lobe causal sign.

**Evidence**
- `linear_cross_real_contribution` = `0.0499104`
- `full_early_log_growth` = `0.139996`
- `without_cross_early_log_growth` = `-0.0376388`
- `nonlinear_full_minus_without_cross_growth` = `0.177635`
- `full_core_event` = `n/a`
- `without_cross_core_event` = `n/a`

**Criterion**
- `same_sign_required` = `True`
- `minimum_absolute_growth_difference` = `0.0001`

### G12_TBK_mode_resolved — Coupled torsion–breathing–Kelvin mode resolved
**Role:** `diagnostic`  
**Verdict:** `PASS`  
**Question:** Does the selected oscillatory reduced mode contain non-negligible breathing, torsion and Kelvin participation simultaneously?

**Conclusion:** A genuinely mixed torsion–breathing–Kelvin oscillatory mode is resolved in the expanded basis.

**Evidence**
- `selected_eigenvalue` = `{re: -0.00205096, im: 1.12318}`
- `family_participation` = `{tilt: 0.13136, breathing: 0.144546, torsion: 0.0784044, kelvin: 0.645689}`
- `minimum_TBK_participation` = `0.0784044`
- `coupled_jacobian_convergence` = `0.0149649`

**Criterion**
- `coupled_family_participation_min` = `0.02`
- `coupled_jacobian_convergence_max` = `0.3`

### G13_torsion_coupling_stabilizes — Torsion-coupling stabilization
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Does removing off-diagonal torsion coupling increase the worst coupled-mode growth rate?

**Conclusion:** Torsion coupling is not shown to provide the preregistered stabilizing growth reduction.

**Evidence**
- `growth_penalty_when_torsion_decoupled` = `-0.0901369`

**Criterion**
- `family_coupling_stabilization_min` = `0.01`

### G14_kelvin_coupling_stabilizes — Kelvin-coupling stabilization
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Does removing off-diagonal Kelvin coupling increase the worst coupled-mode growth rate?

**Conclusion:** Kelvin coupling is not shown to provide the preregistered stabilizing growth reduction.

**Evidence**
- `growth_penalty_when_kelvin_decoupled` = `-0.157847`

**Criterion**
- `family_coupling_stabilization_min` = `0.01`

### G15_breathing_coupling_stabilizes — Breathing-coupling stabilization
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Does removing off-diagonal breathing coupling increase the worst coupled-mode growth rate?

**Conclusion:** Breathing coupling is not shown to provide the preregistered stabilizing growth reduction.

**Evidence**
- `growth_penalty_when_breathing_decoupled` = `-0.000740752`

**Criterion**
- `family_coupling_stabilization_min` = `0.01`

### G16_TBK_collective_coupling_stabilizes — Collective TBK coupling stabilization
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Does block-diagonalizing all mode families increase the worst growth rate relative to the fully coupled system?

**Conclusion:** The fully coupled TBK system is not more stable than the family-block-diagonal counterfactual by the preregistered margin.

**Evidence**
- `growth_penalty_when_all_families_block_diagonalized` = `-0.157847`

**Criterion**
- `collective_coupling_stabilization_min` = `0.02`

### G17_TBK_phase_lock — Torsion–breathing–Kelvin phase locking
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Along the best recurrence trajectory, do dominant breathing, torsion and Kelvin coordinates frequency-lock with stable relative phase?

**Conclusion:** No sufficiently coherent torsion–breathing–Kelvin phase lock is resolved over the tested trajectory.

**Evidence**
- `phase_lock_valid` = `False`
- `phase_lock_strength` = `nan`
- `relative_frequency_spread` = `nan`
- `pair_phase_locks` = `n/a`

**Criterion**
- `phase_lock_strength_min` = `0.65`
- `phase_frequency_spread_max` = `0.25`

### G18_RPO_recurrence — Relative-periodic-orbit recurrence
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** After removing rigid motion, does a phase-scanned coupled perturbation return sufficiently close to its initial shape without a near-core event?

**Conclusion:** No tested phase returns close enough to establish an RPO candidate under the preregistered threshold.

**Evidence**
- `excursion_reached` = `False`
- `peak_before_return` = `n/a`
- `return_ratio` = `n/a`
- `best_recurrence` = `nan`
- `best_period_steps` = `n/a`
- `best_period_time` = `n/a`
- `core_event` = `n/a`

**Criterion**
- `rpo_excursion_min` = `0.01`
- `rpo_recurrence_max` = `0.05`
- `rpo_return_ratio_max` = `0.65`
- `core_event_required_absent` = `True`

### G19_Floquet_bounded — Nonlinear return-map Floquet boundedness
**Role:** `diagnostic`  
**Verdict:** `FAIL`  
**Question:** Conditional on a passing RPO recurrence, are the finite-difference return-map multipliers bounded after excluding one neutral multiplier nearest unity?

**Conclusion:** No valid RPO-conditioned Floquet test is available, or at least one tested non-neutral multiplier exceeds the preregistered bound.

**Evidence**
- `floquet_valid` = `False`
- `reason` = `no_rpo_candidate`
- `spectral_radius_excluding_neutral` = `nan`
- `period_steps` = `n/a`
- `period_time` = `n/a`

**Criterion**
- `floquet_requires_RPO_recurrence` = `True`
- `floquet_spectral_radius_max` = `1.05`

### Orientation/contact synthesis
- Distinct close-contact cross-lobe separating fraction: `0.583333`.
- Median cross-lobe separation rate across those contacts: `0.0701965`.
- Correlation of separation rate with antiparallelness: `0.0374554`.
- Lobe-centroid pair separating fraction: `0.333333`.