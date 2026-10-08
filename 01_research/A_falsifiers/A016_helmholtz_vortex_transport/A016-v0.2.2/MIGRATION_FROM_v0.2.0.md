# Migration to A016-v0.2.2

v0.2.0 used a direct `KnotPlot/knots/final` path and its real run stopped at G1 because that path was absent. v0.2.1 correctly introduced provider-level X0 logic, but preregistered a non-existent E010-v0.4.0 publication-ready dependency, so its real run also stopped at G1.

Drive/Workbench inspection shows the actual production chain is E010-v0.3.1 -> E011-v0.3.0. E011 is explicitly the falsifier-facing STATIC_READY seed atlas and its real production run passed with 34 STATIC_READY topologies, 431 primary carriers and 47 deterministic provider anchors.

v0.2.2 therefore changes only the source/admission/staging architecture. H0–H4, P0–P6, X0 thresholds, backend parity tolerance and continue-after-scientific-failure semantics remain unchanged.

The old v0.2.0/v0.2.1 runs remain immutable audit evidence. Their G0/G2/P0/P1/P2/B0 results may be used as regression context, but neither run produced source-dependent H/P/X0 evidence because G1 failed before any geometry sample was admitted.
