# Pre-registered conditioning protocol

1. Parse PD and independently cross-check component count from Gauss code when available.
2. Build the v1 crossing-correct PD scaffold.
3. Uniformly resample every closed component and normalize global radius of gyration to one.
4. Try Fourier bandwidth H=1,2,... in ascending order. H=1 may be circularized in its own plane.
5. Accept the first H that simultaneously:
   - preserves component count;
   - preserves the integer-rounded pairwise Gauss linking matrix;
   - keeps numerical homotopy clearance above the frozen minimum;
   - reduces RMS turning angle by the frozen factor.
6. If no candidate passes, emit `FALLBACK_RAW_UNIFORM`; do not optimize against dynamics.

No vortex evolution metric participates in selection.
