# Dataset Scanner Trust Model — v0.2.4

The scanner is an inventory/discovery layer, not a proof that every file below a project root is geometry.

## Status semantics

- `OK`: a supported centerline geometry format was decoded and canonical geometry hashes were produced.
- `SKIPPED_METADATA`: a known provider metadata artifact (for example `0TwelveData.csv`).
- `SKIPPED_NON_GEOMETRY`: a selected file that is not an admissible knot/link centerline. This includes
  unrelated project text and Ridgerunner auxiliary VECT products such as `*.struts.vect`, `*.dlen.vect`
  and `*.dVdt.vect`.
- `ERROR`: a file had a strong centerline geometry signature/name but decoding failed. This remains fail-closed.

## Discovery counters

`discovered_file_count` counts every file recursively below the requested root.

`selected_file_count` / `file_count` count files whose suffix or special name is relevant to the scanner.

`ignored_extension_counts` reports files not selected for parsing, grouped by suffix.

`ignored_extension_examples` reports up to five relative paths per ignored extension. This is intended for
safe onboarding of unknown archives without guessing their syntax.

## Geometry candidate signatures

Strong signatures include:

- `KnotPlot 1.0` binary header;
- Geomview/plCurve `VECT` or `4VECT`;
- Brian Gilbert `<AB>`/`<HT>` plus `<Coeff>` Fourier records;
- `.xyz`, `.vect`, `.knot`, `.kp`, `.kpf`;
- extensionless `fseries` and `ideal` / `ideal.txt` names.

For ordinary `.txt` and `.csv`, the scanner samples content and requires at least three finite XYZ-like
numeric rows before attempting the full geometry parser. A topology-bearing name such as
`knot_6.2_final.txt`, `link_6.2.1_final.txt` or `torus_3.6_final.txt` remains a strong claim: if such a
file is malformed, it is an `ERROR`, not a skip.

## Ridgerunner VECT boundary

Ridgerunner uses plCurve, whose disk format is the human-readable Geomview VECT format. VECT files may
contain `#` comments; v0.2.4 removes comments before tokenization and accepts both `VECT` and `4VECT`.
Negative per-polyline vertex counts indicate closed polylines in the conventional VECT representation.

Ridgerunner also emits auxiliary VECT products. Contact struts and step diagnostics are valuable analysis
artifacts, but they are not the knot centerline. Therefore files matching these suffixes are excluded from
centerline admission:

- `*.struts.vect`
- `*.dlen.vect`
- `*.dVdt.vect`

They can be supported later by a dedicated Ridgerunner-diagnostics adapter without weakening the centerline
trust boundary.

References:

- plCurve: https://jasoncantarella.com/wordpress/software/plcurve/
- Ridgerunner: https://jasoncantarella.com/wordpress/software/ridgerunner/
- Geomview VECT format summary: https://paulbourke.net/dataformats/oogl/

## Inventory history

`run_dataset_inventory.cmd <root>` produces a timestamped report such as:

```
outputs\dataset_inventories\final_20260830_143800.json
```

and copies the newest report to:

```
outputs\dataset_inventory.json
```

Use an explicit second argument when a stable output path is required.
