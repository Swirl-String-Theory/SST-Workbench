# Relaxed-knot input contract

Accepted input is a text centerline with at least three whitespace-separated floating-point columns `x y z`. Blank lines separate link components. A repeated first point at the end is accepted and removed. The campaign treats each component as closed even when the repeated endpoint is omitted; `H0-GEOMETRY` checks whether the implicit closing edge is commensurate with ordinary edges.

The default Windows dataset directory is:

```text
C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

Normal and extended campaigns first search `*_final.txt` and fall back to `*.txt` only if no final files are present.

No filename, knot label, electron assignment, or target constant is used by blind scoring.
