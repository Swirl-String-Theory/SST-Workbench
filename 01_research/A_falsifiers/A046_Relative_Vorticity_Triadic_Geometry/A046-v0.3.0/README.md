# A046 v0.3.0 — E011/PKLSA field bridge

Additive scientific *diagnostic* extension of existing A046 v0.2.0. Does not overwrite its 21 verified synthetic gates. Uses regularized finite-segment Biot–Savart velocity (circulation normalized to 1) on a Cartesian grid, periodic Helmholtz projection, strain/vorticity, and pressure-Poisson inversion. Since free-space velocity is projected as a periodic field, this **does not certify physical pressure boundary conditions**, gravity, temporal Euler solution, or knot stability.

Run:
```
run_all.cmd SELFTEST
run_all.cmd DRYRUN --csv C:\path\E011\trefoil.csv
run_all.cmd CERTIFY --csv C:\path\E011\trefoil.csv --meta C:\path\E011\trefoil.provenance.json
```

Provenance JSON schema (source-produced, not a self-certification of independence):
```
{"source_class":"E011_PKLSA","upstream_sha256":"<actual SHA-256 of CSV>","independence_group":"<real upstream group>","topology":"3_1"}
```

CSV must be a closed centerline with x,y,z columns or three numeric comma-separated columns; >=16 nondegenerate points, dimensional scale retained in output but calculation is dimensionless. The `DRYRUN` mode cannot serve as a physical certification. Recompute for at least two distinct upstream providers and a qualified time-dependent Euler source before promoting scientific claims.

`G4_GRID_CONVERGENCE` can FAIL for real geometry: this is a scientific/numerical finding, not a reason to change post-hoc tolerances. `G5/G6/G7/G8` remain open by construction. Every run writes a new non-overwriting output directory, with hashes and raw metrics.
