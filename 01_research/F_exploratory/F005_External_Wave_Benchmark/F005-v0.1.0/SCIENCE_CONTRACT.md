# SCIENCE CONTRACT v0.1.0

**Status: DEVELOPMENT / ANALYTICAL REGRESSION ONLY / NOT CERTIFIED.**

## Observables
- KELVIN: complex lateral displacement eta(z,t) of the physical core boundary, mean core radius, independently measured circulation and axial flow, dispersion omega(k,m), spectral amplitude, pentacoherence.
- INERTIAL: two-component PIV in vertical light-sheet plane, rotation omega, wave vector theta, frequency in rotating frame, independent correlations of u_x and u_r.
- BUBBLE VIDEO: bright centroid or bubble transport is **NOT** native eta(z,t) or PIV without an independent calibration.

## Frozen controls
- SI dimensions with source-specific sign convention. The one source reports negative v_z for its convention.
- Kelvin Eq (7) *hollow-core* is not the implicit Rankine Eq (1); v_z is absent. Compare like for like only.
- a0=1.47 mm belongs to Kelvin paper Fig 2; a0=1.3 mm to other conditions in Figs 3,4. Never mix.
- Inertial relation applies in nearly uniformly rotating frame; not universally to any vortex.
- no tuning of free parameters to the same experimental dispersion used as a test.
- No immediate microscopic SST core mapping: laboratory millimeter-scale core != canonical r_c.
- Pre-declare independent holdout experimental records before running PKLSA.
- Source-native >= digitized graph with errors >= literature-only plot (evidence hierarchy).

## Gate semantics
G0-3 PASS = provenance and analytical tests only. G4-7 blocked while native arrays absent.
G8 NOT_RUN = no independently computed PKLSA prediction. G9 UNRESOLVED = cannot promote SST physical claims.

## External datasets that would unlock gates
1. PRL Barckicke et al: author-requested eta(z,t), eta_k(t) 75-minute complex amplitudes, PIV circulation and uncertainty. Paper states source data not public.
2. JFM Jackson & Thomas: u,v PIV cubes, rotation records, spatial calibration, PIV covariance/errors, separate runs; supplementary public videos are not numeric PIV cubes.
3. Optional third dataset: Nature Physics 2026 Barckicke et al, Figshare DOI 10.6084/m9.figshare.30903347, **not yet imported, decoded or integrity-tested**.

## Pre-registration candidate validation thresholds
- median standardized residual (omega_pred-omega_obs)/sqrt(sigma_obs^2+sigma_pred^2) and 95% coverage; 90% of independent held-out frequencies within 2 sigma (only when uncertainty model available).
- original source reported dispersion convention, Doppler and azimuthal m transforms must be accounted for.
- for six-wave pentacoherence: phase-shuffled null, FDR <= 0.01; sufficient independent windows with covariance, avoid pseudo-independent Fourier bins.
- Require comparisons against Euler/Rankine or standard inertial model; a match alone does not favor SST.
- A negative case: data matching classical baseline and no source-native SST-predictive output -> UNRESOLVED SST, not PASS.
