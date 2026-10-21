# SCIENCE CONTRACT — v0.4.3a beadlimit

- **Scope:** simulator runtime capacity only; no changes to XYZ geometry, sources, dynamics parameter values, scalar measurements, or knot/link labels.
- **Actual bead count:** sum over all loaded XYZ components. For single knots, its unique point count.
- **Threshold:** add `go beadlimit <limit>` only if total count exceeds 3000.
- **Ordering:** `load` then `go beadlimit ...` (when required) then `ago`.
- **Repeatability:** SHA-256 of generated protocol changes when high-N capacity changes, preventing unreviewed reuse of older KPC paths. At <=3000, protocols and scripts stay byte-for-byte identical to v0.4.3.
- **Safety:** original module is backed up; patch aborts on unknown previous source, duplicate installation, or unsupported layout.
- **Runtime status:** local Windows/KnotPlot execution remains unverified.
- **Claims not warranted:** topology preservation, Borromean Milnor invariant, fluid Euler dynamics, or dynamical convergence.
