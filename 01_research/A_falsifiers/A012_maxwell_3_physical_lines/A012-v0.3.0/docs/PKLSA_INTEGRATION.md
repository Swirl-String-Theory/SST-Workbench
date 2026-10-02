# PKLSA-v0.3.x integration contract

The v0.3.0 falsifier was designed against the current E010 `v0.3.1` Workbench release inspected from Google Drive.

Runtime authority order:

1. live E010 production `RELEASE.json`;
2. per-topology `qualification/summary.json`;
3. per-topology `qualification/geometry_metrics.json`;
4. per-topology source-independence ledger;
5. per-carrier `CAR_*.json` envelope;
6. the original source bytes referenced by the envelope.

The package never scans `03_data/A_knots` and decides for itself which files are scientific carriers. E010 owns that classification.

## Independence discipline

`independence_group`, `provider_group`, `method_group` and `lineage_group` are provenance strata, not replicated experimental measurements. Byte-identical mirrors and declared duplicate geometries are excluded by default. Generated PTSA/QHP-derived material can be useful as a geometry/control carrier but is not silently counted as a new upstream provider.

## Core-radius convention

E010 emits `reach` and `Thi = 2*reach`. Maxwell-3 uses **`reach` as the radius** of the finite-core sampling tube. It does not treat `Thi`/`thickness` as a radius.

## Topological anti-circularity

E010 target:

- exact polygonal segment-pair solid-angle integration for `Lk`.

Maxwell-3 observable:

- independent midpoint-segment Biot--Savart integration followed by a closed probe-loop line integral.

Thus the target and observable do not call the same computational kernel.
