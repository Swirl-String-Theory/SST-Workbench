# SST Geometry Field Clock Covariance Blind Falsifier v0.1.0

This package implements a dimensionless, provenance-clean blind test of whether closed vortex microgeometry plus incompressible pressure-Poisson closure produces robust finite-volume covariance scaling beyond an uncorrelated spatial null.

## Blind rule

The executable blind path contains no calibrated SST constants, no absolute physical units, no target exponent, and no post-hoc parameter fitting to an SST prediction. Geometry is centered and normalized from its own coordinates. The vector field is normalized by its own RMS amplitude before the scalar closure is evaluated.

The primary scalar closure is

    laplacian(q) = - d_i u_j d_j u_i

on a periodic numerical box after a spectral divergence-free projection. For each averaging radius R, the code measures the variance of the spherical finite-volume average and fits

    Var[q_R] ~ R^(-n_space)

without assigning a theory label to n_space. A voxel-shuffled null is analyzed with the same pipeline. The blind verdict asks only whether correlated closure scaling is resolved, differs from the uncorrelated null by a preregistered margin, and survives numerical qualification.

A secondary diagnostic evolves the closed filament in dimensionless time and measures the variance of the integrated local scalar residual across fixed probes.

## Quick run

Windows:

    run_setup.cmd
    run_all.cmd

Python-only reference run:

    python -m sst_gfcc_blind.cli --config config/default.json --out SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.1.0-outputs

## Output interpretation

The BLIND output does not map measured exponents to named external models. Run `run_reveal.cmd` only after `blind_results.json` is frozen and hashed.

## Scope

v0.1.0 is a self-contained reference campaign. It uses four generated closed-curve families so it can run without the Workbench datasets. Production certification should replace or augment those curves with PKLSA / relaxed / ideal library geometries while preserving the same blind analysis and configuration freeze.
