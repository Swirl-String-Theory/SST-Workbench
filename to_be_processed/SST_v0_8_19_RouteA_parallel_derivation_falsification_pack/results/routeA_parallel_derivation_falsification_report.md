# Route A parallel derivation/falsification report
Status: `[RESEARCH-TRACK] [PREREGISTERED] [FALSIFICATION-HARNESS]`
## Target
- sigma_pierce Lambda_L target: `1.914036558578934e+69 m^-2`
- target spacing if sigma=1: `2.285729775093407e-35 m`
- reference Planck time: `5.391246446661944e-44 s`

## Model outcomes
### O1_core_cutoff_one_per_rc2
Family: `Onsager/KT-like vortex gas`  
Status: `FAIL_DERIVED_SCALE_TOO_SMALL`  
Formula: `sigmaLambda = r_c^{-2}`  
sigmaLambda = `5.037283605853596e+29 m^-2`  
ratio to target = `2.631759348208845e-40`  
log10 ratio = `-39.579754`  
t_model/t_ref = `6.164202721393094e+19`  
Note: Maximal naive one-core-per-area sheet density. Misses Planck target by ~40 orders; no G/Lp/tp input.

### O2_disk_packing_one_per_pi_rc2
Family: `Onsager/KT-like vortex gas`  
Status: `FAIL_DERIVED_SCALE_TOO_SMALL`  
Formula: `sigmaLambda = (pi r_c^2)^{-1}`  
sigmaLambda = `1.603417171254733e+29 m^-2`  
ratio to target = `8.377150185914846e-41`  
log10 ratio = `-40.076904`  
t_model/t_ref = `1.092576485129545e+20`  
Note: Densest non-overlap tube cross-section estimate. Even smaller than O1.

### S1_crofton_projection_factor_only
Family: `Crofton/stereology`  
Status: `PARTIAL_LEMMA_ONLY_NO_SCALE`  
Formula: `<N_pierce>/A = <|cos theta|> Lambda_L = (1/2) Lambda_L`  
Note: Monte Carlo <|cos theta|>=0.499892882; analytic value is 1/2. This proves the projection factor, not Lambda_L.

### S2_crofton_plus_core_packing
Family: `Crofton/stereology`  
Status: `FAIL_SCALE_INPUT_CORE_PACKING_TOO_SMALL`  
Formula: `sigmaLambda = (pi r_c^2)^{-1}; N/A = Lambda_L/2`  
sigmaLambda = `1.603417171254733e+29 m^-2`  
ratio to target = `8.377150185914846e-41`  
log10 ratio = `-40.076904`  
t_model/t_ref = `1.092576485129545e+20`  
Note: Stereology maps line density to piercings. If Lambda_L is only core packing, target is missed by ~40 orders.

### T1_single_3D_Weyl_channel
Family: `torsion-channel phase-space`  
Status: `FAIL_PRE_REGISTERED_Weyl3D_TOO_SMALL`  
Formula: `sigmaLambda = r_c^{-2}(rho_core/rho_f)[2/(6 pi^2)](c/v)^3`  
sigmaLambda = `1.948069218606952e+60 m^-2`  
ratio to target = `1.017780569485718e-09`  
log10 ratio = `-8.992346`  
t_model/t_ref = `3.134533547541494e+04`  
Note: Direct 3D Weyl channel count with two transverse polarizations. Non-fit; misses target by many orders.

### T2_paired_3D_Weyl_channels
Family: `torsion-channel phase-space`  
Status: `FAIL_PRE_REGISTERED_WeylPair_TOO_SMALL`  
Formula: `sigmaLambda = r_c^{-2}(rho_core/rho_f)[2/(6 pi^2)]^2(c/v)^6`  
sigmaLambda = `1.354494932272093e+66 m^-2`  
ratio to target = `7.076640862480343e-04`  
log10 ratio = `-3.150173`  
t_model/t_ref = `3.759122011901788e+01`  
Note: Paired in/out or two-boundary Weyl count. Gets exponent 6 without a scan but coefficient is ~1.4e3 too small.

### T3_archived_seed_16_over_pi2
Family: `torsion-channel phase-space`  
Status: `TRIAL_FITTED_NEGATIVE_CONTROL_NOT_DERIVED`  
Formula: `sigmaLambda = r_c^{-2}(rho_core/rho_f)(16/pi^2)(c/v)^6`  
sigmaLambda = `1.925039396852048e+69 m^-2`  
ratio to target = `1.005748499538213e+00`  
log10 ratio = `0.002489`  
t_model/t_ref = `9.971380831328669e-01`  
Note: Earlier seed relation. Included only as look-elsewhere controlled negative control; kernel/exponent not independently derived.

## Verdict
Crofton/stereology derives the 1/2 factor only. Onsager/KT core packing fails by ~40 orders. Strict Weyl/torsion phase-space models fail by 3--9 orders. The old 16/pi^2 seed remains a fitted negative control, not evidence.

## Key falsification numbers
- Required BKT single-density multiplier y: `3.799739519043001e+39`
- Required BKT pair fugacity y: `6.164202721393093e+19`
- Required exponent-6 kernel K: `1.611873086583521e+00`
- Strict paired-Weyl kernel: `1.140664694964926e-03`
- Multiplier needed over paired Weyl: `1.413099830036454e+03`
