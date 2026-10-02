# Reproducibility and immutable release history

## Goal

A single v0.3.0 archive contains the exact current inputs plus immutable prior release archives so the older conclusions can be recomputed from their original code/configuration rather than copied from old JSON.

## Bundled canonical inputs

```text
repro_inputs/knot.3_1.fseries
repro_inputs/knot_3.1_final.txt
```

Their SHA-256 hashes are stored in `repro_inputs/INPUTS.sha256`.

Normal campaign scripts still default to the working-copy paths under

```text
C:\workspace\projects\SST-Workbench\KnotPlot\...
```

The bundled files are used only for historical/reproducibility runs unless supplied explicitly.

## Bundled immutable releases

```text
release_history/SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.1.0.zip
release_history/SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.1.1.zip
release_history/SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.2.0.zip
```

Their hashes are recorded in `release_history/INDEX.sha256`. Do not edit these archives.

The v0.2.0 archive already contains its own v0.1.x history, but v0.3.0 also keeps direct v0.1.x copies so every historical snapshot is one lookup away.

## Recalculate all conclusions

BASIC:

```bat
run_reproduce_history_basic.cmd
```

EXTENDED:

```bat
run_reproduce_history_extended.cmd
```

The reproduction driver:

1. verifies/uses the bundled inputs;
2. extracts each archived release into `_history_work/`;
3. creates an isolated `.venv_history` for that release;
4. installs that release's original `requirements.txt`;
5. executes its own `run_blind.py` and original BASIC/EXTENDED config;
6. runs v0.3.0 last against the same inputs;
7. writes results and a reproduction manifest under `_history_results/`.

Historical runs use the Python reference backend for deterministic cross-version portability. Production runs can use the native OpenMP/SYCL backends.

## Decision-rule continuity

The overall critical gate set remains

```text
G0, G2, G3, G4, G6
```

through v0.1.0, v0.1.1, v0.2.0 and v0.3.0.

v0.2 adds G7–G11 diagnostics; v0.3 adds G12–G19 diagnostics. These can deepen or falsify mechanistic interpretations without retroactively changing the original campaign PASS/FAIL definition.

## New-version policy

For every subsequent release:

- preserve the exact immediately previous release ZIP;
- retain all earlier immutable snapshots directly when practical;
- keep `CHANGELOG.md` cumulative;
- keep `docs/HISTORICAL_REFERENCE_CONCLUSIONS.md` cumulative;
- keep source-input hashes and release hashes;
- do not overwrite old configs or gate wording.
