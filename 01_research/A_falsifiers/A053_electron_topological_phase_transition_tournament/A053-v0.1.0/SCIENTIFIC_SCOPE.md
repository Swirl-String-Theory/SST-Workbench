# Scientific scope and assumptions

## Blind assumptions

The blind stage is dimensionless. It assumes only:

- closed polygonal vortex centerlines;
- a producer-declared finite-core or ideal-filament model;
- dimensionless circulation sectors fixed before execution;
- a target-blind external interaction protocol;
- objective time windows: pre, pulse, post;
- topology/provenance metadata sufficient to distinguish one- and two-component sectors.

## Not assumed

The blind stage does not assume:

- an electron mass or Compton scale;
- \(\alpha\), \(r_c\), \(\rho_f\), or \(\mathbf v_{\circlearrowleft}\);
- that any knot or link is an electron;
- that a photon is literally a vortex link;
- that quantum measurement is explained by reconnection;
- a target transition frequency;
- a preferred winner among H0--H3.

## Falsifiable predictions

H0 predicts topology persistence of `3_1` through the standardized interaction.

H1 predicts topology persistence of `L2a1` plus independently observed post-interaction mode locking.

H2 predicts an interaction-correlated, target-blind topological event with \(|Lk|\) changing from approximately 1 to approximately 2.

H3 predicts an interaction-correlated temporary multi-component interval carrying \(|Lk|\approx1\) or 2, followed by return to the one-component electron sector.

## Edge cases

A topology-changing result from an `ideal_euler_no_reconnection` producer is treated as an implementation error or undeclared numerical topology surgery.

A run with missing independent phase data cannot support H1.

A link transition seen equally in sham controls cannot support H2/H3.

A result that appears at one resolution but does not converge is `INDETERMINATE_NUMERICS` or `FAIL_TESTED_DOMAIN`, according to whether the prerequisite resolution ladder completed.
