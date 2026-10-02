# v0.4.1 Full-Archive Preregistration

## Scope

The archive campaign includes **every** parseable input in the two bundled canonical archives:

- 78 Fremlin `.fseries` files, including every suffix/alternate representation;
- 49 KnotPlot/RidgeRunner `*_final.txt` files, including knots, unlinks, links and torus knots/links;
- total: **127 distinct geometry files**.

No Fremlin suffix variant may be silently replaced by a single representative.

## Unchanged critical gates

The v0.4 generic critical set remains

\[
P0\land P1\land P2\land P5.
\]

`P3`, `P4`, link-only `P6`, `P7` and `P8` are diagnostic/causal gates and do not retroactively change the earlier decision rule.

## EXTRA_EXTENDED

- total resample points: 240;
- Kelvin harmonics: \(k=2,3,4,5,6\);
- finite-difference amplitudes: \(0.0015,0.003,0.006\);
- ringdown: 220 steps;
- Jacobian convergence maximum: 0.20;
- normalized-growth maximum: 0.12;
- link drift maximum: 0.06.

RPO/Floquet is attempted only when normalized growth is at most 0.18. This is a compute precondition, not a PASS criterion.

## FULL

- total resample points: 360;
- Kelvin harmonics: \(k=2,\ldots,8\);
- finite-difference amplitudes: \(0.001,0.002,0.004,0.008\);
- ringdown: 480 steps;
- Jacobian convergence maximum: 0.15;
- normalized-growth maximum: 0.12;
- link drift maximum: 0.04;
- RPO phase count: 12;
- RPO search: 520 steps;
- Floquet subspace: at most 12 modes.

RPO/Floquet is attempted only when normalized growth is at most 0.15. A Floquet verdict is still forbidden unless a genuine excursion-and-return RPO first passes the recurrence gate.

## Blinding

Each campaign deterministically shuffles the selected input list to blind IDs before analysis. File hashes are written before unblinding; source names are released only after all selected analyses have been written.

## Shards

Sharding changes only workload partitioning. Each shard uses the exact same preregistered FULL configuration. Sharded output is descriptive unless all expected shards are present and merged.
