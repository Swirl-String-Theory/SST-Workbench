# Source graph and independence model — v0.2.0

Builder v0.2.0 separates three levels which were previously easy to conflate:

1. **provider group** — upstream source/provider identity;
2. **method group** — construction/relaxation method;
3. **lineage group** — related stages/variants descending from the same source lineage.

The legacy `independence_group` remains for compatibility.

Examples:

- KnotPlot seed, N0600, N1200, near-ideal, continued and final states remain one KnotPlot relaxation lineage.
- Ridgerunner is a distinct numerical method but retains its parent-source lineage when it starts from KnotPlot geometry.
- PTSA's 48 parameter variants remain one generated family, not 48 independent upstream observations.
- Byte-identical Fremlin mirrors are provenance records but add no independent evidence.
- KAtlas-to-braid geometry is a generated topology-derived control, not an upstream KAtlas 3-D embedding.

The output ledger reports carrier count, provider count, method count, lineage count, raw-byte duplicates, geometry duplicates, and evidence class separately.
