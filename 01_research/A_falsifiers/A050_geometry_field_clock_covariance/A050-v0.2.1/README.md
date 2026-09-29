# SST Geometry Field Clock Covariance Blind Falsifier v0.2.1

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

## v0.2.1 long-observation protocol

v0.2.1 is deliberately a **horizon-only extension** of v0.2.0. The default family trajectory is extended from 80 to 320 integration steps (4x) at the same `time_step=0.02` and the same sampling cadence. The return-qualified Floquet search is extended from 80 to 640 steps (8x).

No spatial, temporal-memory, transverse-mode, return, finite-difference, or marginality threshold was relaxed after inspecting v0.2.0. A machine-readable copy of the v0.2.0 gate thresholds is frozen in `config/frozen_gate_thresholds_v0.2.0.json`, and `tests/test_v021.py` verifies that v0.2.1 extends only the unresolved modal/recurrence observation horizons rather than changing acceptance criteria.

The purpose is specifically to resolve whether the coherent transverse phases seen in v0.2.0 accumulate enough phase to satisfy the already-frozen Kelvin gate, and whether a genuine shape recurrence appears before any Floquet multiplier is interpreted.

## Quick run

    run_setup.cmd
    run_all.cmd

Python-only:

    python -m sst_gfcc_blind.cli --config config/default.json --out SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.2.1-outputs

The BLIND archive excludes the reveal directory.
