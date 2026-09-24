# E010 PKLSA Fremlin 8_5 restore + incomplete-mirror fix

Target: `E010-v0.3.0`

This patch refines the final A007/Fremlin handling and bundles the actual `8_5` `.short` centerline supplied by the user.

## Scientific/provenance interpretation

- `knot.8_5.short` is a valid sampled XYZ centerline and is admitted as source geometry.
- The observed local `knot.8_5.fseries` is header/comment-only and has no Fourier coefficient rows. It is therefore retained as an **incomplete mirror artifact**, not admitted as geometry.
- This does **not** claim that upstream Fremlin has no Fourier representation for 8_5; it only records that this local mirror artifact is incomplete.
- Malformed `.fseries` files containing non-comment data are still admitted as candidate geometry and fail closed in the parser.

## Bundled short geometry

- file: `patch_payload/knot.8_5.short`
- SHA-256: `8191f86a491a84c59ef677d07e95c038a90f908b8b925ed69739f9fdc6c27778`
- bytes: `6395`
- XYZ samples: 179
- canonical install target (relative to Workbench):
  `03_data/A_knots/06_knot_library/Sources/FourierSeries_Fremlin/original/8_5/knot.8_5.short`

## Install / run

Extract this ZIP directly into the existing:

`...\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.3.0\`

Then run:

```bat
apply_and_repair_8_5.cmd
```

The wrapper:

1. verifies the bundled `.short` SHA-256;
2. derives the canonical SST-Workbench root;
3. installs the `.short` to the A007/Fremlin original/8_5 directory;
4. backs up an existing different target before replacing it;
5. runs package/regression tests;
6. performs the targeted fail-closed repair of the remaining topology only;
7. rebuilds global ledgers and packages the atlas only if all production gates are green.

If you only want to install the source file without running qualification:

```bat
install_8_5_short.cmd
```
