# Relaxed-knot input contract (v0.2.0)

The default Windows directory is:

`C:\workspace\projects\SST-Workbench\KnotPlot\knots\final`

Accepted geometry files are `*_final.txt`. Each nonblank line must contain at least three floating-point columns `x y z`. A blank line separates link components. Each component is interpreted as a closed polygonal centerline, including the final edge from the last vertex back to the first.

A companion `<stem>.metrics.json` is optional. If it contains `length`, the workbench recomputes polygonal length and checks the preregistered relative mismatch.

The geometry audit is a numerical precondition only. It is not a proof of knot type; use the alias/metrics provenance and independent topology verification for that purpose.
