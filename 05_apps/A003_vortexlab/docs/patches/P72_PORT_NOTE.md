# P7.2 Ideal Volume Transfer — surgical port note

Official `Apply-P7.2.cmd` / `Apply-P7.2.py` refuses this tree: the installer requires parent runtime SHA `1754c2ea…` (clean P7.1 CMD-r2). The working runtime was already `2cdba866…` after P6b discrete + domain comma-shift + relative streamlines + fluid-floor work. A blind payload replace would erase those features.

## What was installed surgically

- Full replace of `apps/web/src/legacy/model-a-ideal-stretch.js` with IdealVolumeTransfer-v0.7.2 (payload SHA matches).
- Model A call sites only in `vortexlab-runtime.js`: `resetState` topology/Gilbert/`Rxy` anchor, tube rebuild `isActiveStatus` + transfer diagnostics, post-accept `observe` gate; `APP_VERSION` → `…-p7-v0.7.2-ideal-volume-transfer`.
- TwistFlow UI merge: P7.2 Model A section + tube-visual readouts/export, while retaining P6b discrete controls and continuum relative-streamline disclaimer.
- `project.json` / docs / `tools/test-ideal-volume-transfer-p72.mjs` / `source-hashes.json` / `verify-parity.mjs` updated for patch id `twist-flow-p7-ideal-volume-transfer` with `idealOnly: false`. Runtime/Twist hashes recomputed for this tree; ruben catalog and current CSS/native/fluid hashes preserved.

## Scientific scope unchanged

Visual/research-track only: equal-`Rxy` convention vs Gilbert ideal for recognized single-component labels. No change to Biot–Savart/LIA, `P.a`, Γ, or contact/CFL. Labels are not an isotopy certificate; N192 remains `REFERENCE_TRANSFER_PREVIEW`.
