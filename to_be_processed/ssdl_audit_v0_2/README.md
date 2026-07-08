# SST SSDL Audit Harness v0.2

Research-track audit harness for the Separatrix Surface-Density Lift (SSDL) route:

\[
\rho_f^{\rm SSDL}
= \frac{\Omega_{\Lambda,0}}{\ell_P}\Pi_0\Lambda_\partial^{-1}\Pi_0[\rho_\Lambda]
\]

For a spherical electron separatrix:

\[
\rho_f^{\rm SSDL}
= \Omega_{\Lambda,0}\left(\frac{R_e}{\ell_P}\right)\rho_\Lambda.
\]

## What this package verifies

Route A verifies numerically that a BEM discretization of the spherical exterior monopole response recovers
\(\Pi_0\Lambda^{-1}\Pi_0[1]\approx R_e\) even under tangential Dirichlet perturbations. This is a numerical consistency check, not a constitutive proof.

Route B verifies the analytic Planck-normal cell count \(N_\perp=R_e/\ell_P\), with a toy finite-difference sanity check. It does not attempt to construct a physical-scale matrix with \(10^{20}\) modes.

## What remains open

- L1: \(\rho_\Lambda\) couples as isotropic normal separatrix source.
- L2: \(\Omega_{\Lambda,0}\) is the correct projection factor, or must be replaced by an SST projection functional.
- L3: \(\ell_P\) is the correct normal resolution thickness.

## Run

```bash
python run_ssdl_audit.py
```

To force Python fallback:

```bash
python run_ssdl_audit.py --force-python
```

## Status

`[RESEARCH TRACK / NUMERICALLY SUPPORTED / CONSTITUTIVE LEMMAS OPEN]`
