# SST Geometry Field Clock Covariance Blind Falsifier v0.2.0

A dimensionless, provenance-clean blind falsifier for four linked questions:

1. Does incompressible pressure-Poisson closure generate finite-volume covariance scaling distinct from a decorrelated spatial null?
2. Does the resulting scalar field retain temporal memory beyond a time-shuffled null?
3. Does the evolving closed filament support a coherent transverse modal component?
4. If and only if a nontrivial return is first resolved, is a finite-dimensional Floquet multiplier estimate numerically convergent?

The blind executable path contains no calibrated SST constants, no absolute physical units, and no theory-specific target exponent or target multiplier. Geometry and fields are normalized internally from each dataset.

## Gates

### Spatial covariance

The scalar closure is

    laplacian(q) = - d_i u_j d_j u_i

and the finite-volume variance is fitted as

    Var[q_R] ~ R^(-n_space).

A voxel-shuffled spatial null is processed identically.

### Temporal memory

Fixed probe signals are spatially averaged and their mean autocorrelation, integrated correlation time, and integrated-residual scaling are measured. A time-shuffled null is generated without any external target value.

### Transverse filament modes

Each evolving curve is rigidly aligned to its initial geometry. Tangential gauge is removed in a discrete Bishop frame. The complex transverse displacement is Fourier-decomposed along arclength, and dominant-mode energy plus phase coherence are measured.

### Floquet

No multiplier is interpreted unless the trajectory first departs from the initial state and then returns to a preregistered residual tolerance. If no such return exists, the gate returns an indeterminate status. For a qualified return, a small transverse basis is perturbed at two amplitudes and a finite-difference monodromy matrix is reconstructed.

## Quick run

    run_setup.cmd
    run_all.cmd

Python-only:

    python -m sst_gfcc_blind.cli --config config/default.json --out SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.2.0-outputs

The BLIND archive excludes the reveal directory.
