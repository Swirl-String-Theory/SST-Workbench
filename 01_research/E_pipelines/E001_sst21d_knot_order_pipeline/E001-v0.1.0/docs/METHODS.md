# Methods and limitations

## Fourier catalogue

For each component,

\[
\mathbf X(t)=\sum_n\left(\mathbf A_n\cos nt+\mathbf B_n\sin nt\right),
\qquad 0\le t<2\pi.
\]

The sampled curve is then periodically resampled to uniform polygonal arclength. The original Fourier curve is not overwritten.

## Static versus dynamic evidence

`ideal_favorites.txt` provides geometry only. It cannot supply:

- phase coherence;
- a Goldstone dispersion;
- damping;
- non-affine rearrangement in time;
- defect percolation;
- lifetime.

Those fields require a trajectory and, for phase order, an explicit phase/material-frame field.

## Topology

The package preserves catalogue IDs and can merge KnotPlot sidecars containing `safe`, component counts, and linking matrices. It does not independently compute Alexander/HOMFLY polynomials or a certified knot type. A no-crossing continuity gate is not equivalent to a topological proof.

## Ridgerunner

The package can export valid closed VECT files and ingest polished outputs. It deliberately delegates relaxation to the user's existing tested three-stage Ridgerunner pipeline. The bridge script does not replace seed-selection, `safe`, `lnknum`, residual, or plateau gates.
