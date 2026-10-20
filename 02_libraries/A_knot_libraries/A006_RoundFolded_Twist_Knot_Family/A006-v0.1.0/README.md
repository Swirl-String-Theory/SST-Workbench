# RoundFolded Twist Knot Family v0.1.0

Reproducible **static geometry candidates** for the twist-knot family `T_m = C(m,2)` and decorated Borromean 3-component links. **No Euler dynamics or certified topology.** See [ROUND_FOLDED_FAMILY_SPEC.md](ROUND_FOLDED_FAMILY_SPEC.md) for complete mathematical, numerical, and validation details.

On Windows, in the extracted project root:

- `run_all.cmd BASIC` — four isolated twists plus `5_2 + 5_2 + 6_1` Borromean; 256 source samples and uniformized outputs.
- `run_all.cmd FULL` — same cases with 512 source samples, higher output resolution.
- `run_all.cmd BORROMEAN` — Borromean only.
- `run_all.cmd ACQUIRE` — prepares KnotPlot-local Conway `.kpc` acquisition scripts (does not itself run KnotPlot).

To view in KnotPlot (working directory is extracted root):

```
read output/individual/Tm3_5_2_N0256/Tm3_5_2_N0256_LOAD.kpc
read output/borromean/Borromean_5_2_5_2_6_1_N0256/Borromean_5_2_5_2_6_1_N0256_LOAD.kpc
```

Run `py -3 -m unittest discover -s tests -v` to inspect nine regression tests. All source SHA256 sums appear in `SHA256SUMS.txt` and each `REPORT.json`. Read-only inputs from historical KnotPlot exports are included unmodified, with no automatic relaxations. Rebuild does not overwrite user source files or frozen falsifiers.

**KnotPlot `go` is knot-length relaxation, NOT incompressible Euler vortex motion.** Geometry acceptance remains pending independent knot-polynomial and Borromean triple-invariant certification.
