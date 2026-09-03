# Dataset Scanner Trust Model — v0.2.3

The scanner is an inventory/discovery layer, not a proof that every file below a project root is geometry.

## Status semantics

- `OK`: a supported geometry format was decoded and canonical geometry hashes were produced.
- `SKIPPED_METADATA`: a known provider metadata artifact (for example `0TwelveData.csv`).
- `SKIPPED_NON_GEOMETRY`: a file selected by broad suffix rules but lacking a supported geometry
  signature. This is normal in whole-project scans.
- `ERROR`: a file had a strong geometry signature/name but decoding failed. This is intentionally
  fail-closed and requires investigation.

## Discovery counters

`discovered_file_count` counts every file recursively below the requested root.

`selected_file_count` / `file_count` count files whose suffix or special name is relevant to the scanner.

`ignored_extension_counts` reports files not selected for parsing, grouped by suffix. This is especially
useful when onboarding a new external dataset: a zero selected count is no longer ambiguous.

## Geometry candidate signatures

Strong signatures include:

- `KnotPlot 1.0` binary header;
- `VECT` header;
- Brian Gilbert `<AB>`/`<HT>` plus `<Coeff>` Fourier records;
- `.xyz`, `.vect`, `.knot`, `.kp`, `.kpf`;
- extensionless `fseries` and `ideal` / `ideal.txt` names.

For ordinary `.txt` and `.csv`, the scanner samples content and requires at least three finite XYZ-like
numeric rows before attempting the full geometry parser. A topology-bearing name such as
`knot_6.2_final.txt`, `link_6.2.1_final.txt` or `torus_3.6_final.txt` remains a strong claim: if such a
file is malformed, it is an `ERROR`, not a skip.

## Inventory history

`run_dataset_inventory.cmd <root>` now produces a timestamped report such as:

```
outputs\dataset_inventories\final_20260830_143800.json
```

and copies the newest report to:

```
outputs\dataset_inventory.json
```

Use an explicit second argument when a stable output path is required.
