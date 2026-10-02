# PKLSA v0.3.0 architecture

The evidence chain is deliberately layered:

```text
raw source bytes
  -> source identity + SHA-256
  -> topology/reference identity
  -> concrete centerline carrier
  -> canonical numerical reconstruction
  -> resolution ladder
  -> geometry observables + convergence
  -> source-independence ledger
  -> downstream SST dynamics
```

## Carrier identity

A carrier is not a filename. It has `carrier_id`, `topology_id`, `source_family`, `source_role`, `representation`, `variant_id`, `independence_group`, optional parent lineage, raw SHA-256, and source metadata.

An algorithmic transformation does not erase ancestry. For example:

```text
KnotPlot seed -> Ridgerunner relaxer -> RR final VECT
```

is a useful cross-method carrier, but it is not independent of the KnotPlot input in the same sense as an independently published Gilbert/Fremlin/KnotInfo embedding.

## Trefoil ensemble

The operational `3_1` ensemble is open-ended. The builder expects at least the families named in the root README but records zero coverage rather than manufacturing a missing carrier. This is important for historical SIAF controls: if no `3_1` SIAF source is present in the selected base/Workbench, `source_matrix.csv` reports zero.

## Reference layer vs geometry layer

KnotInfo/KAtlas fields may tell us what topology a source record claims. A geometry carrier is the concrete curve being measured. The builder never promotes a source label to a curve-level topological proof.
