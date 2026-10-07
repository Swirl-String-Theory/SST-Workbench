# A054-v0.3.0 — Broad Low-Crossing Knot/Link Candidate Blind Falsifier

This release expands A054 from the historical 5_2/6_1 pair to a target-blind low-crossing topology discovery tournament.

BASIC contains 101 anonymous three-component geometries: all 14 prime knots through 7 crossings embedded homogeneously in four source-native KnotPlot three-link skeletons, unlinked controls, the historical mixed 5_2/6_1 permutations, and seven direct source-native three-component links including T(6,9), T(6,15), and T(6,21).

The package includes the user's source-native KnotPlot final exports. For 7_5, 7_6, and 7_7, which were absent from the current `knots/final` folder, self-contained Gilbert `Ideal.txt.gz` record samples are included with record provenance. These are not silently treated as the same provider as KnotPlot.

Run on Windows:

```bat
run_discovery_basic.cmd
```

Inspect BLIND outputs first. Reveal only afterward:

```bat
run_99_reveal_discovery.cmd
```

The discovery stage is not final dynamical certification. Promising candidates should be passed into the unchanged v0.2.0 restoring-force × Kelvin/ringdown × conditional RPO/Floquet stack under multiple geometry-provider/embedding variants.
