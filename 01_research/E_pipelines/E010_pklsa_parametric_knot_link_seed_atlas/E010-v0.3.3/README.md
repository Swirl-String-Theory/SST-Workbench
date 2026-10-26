# E010 PKLSA Multi-Seed Filter v0.3.4 — hotfix 1

## What was fixed

The original `build_multiseed_view.py` incorrectly expected `TOPOLOGY_SET.json` and `TOPOLOGY_IDENTITY_ADMISSION.json` at the root of the E010 v0.3.1 production outputs. In the canonical production runner they are written to `preflight/`. Both file reads and provenance SHA-256 recording now use the correct relative paths. The selection policy and the untouched historical source outputs are unchanged.

## Install (Windows, in your current E010-v0.3.3 folder)

Extract this ZIP **directly into** `E010-v0.3.3` so `build_multiseed_view.py` replaces the previous version (keep a backup of the old script if desired). This ZIP deliberately places the script at the top level. No atlas files must be copied or moved.

Run in an activated Python environment (PowerShell or CMD), as one line:

```powershell
python .\build_multiseed_view.py --source "..\E010-v0.3.1\E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs" --dry-run
```

Then, if the dry-run succeeds:

```powershell
python .\build_multiseed_view.py --source "..\E010-v0.3.1\E010_PKLSA_Production_Knot_Link_Basis_v0.3.1-outputs"
```

The tool produces `E010_PKLSA_Multiseed_View_v0.3.4-outputs` beside the original campaign output folder and refuses to overwrite it if already present. The original campaign outputs remain unchanged.

## Conditions

- Select topologies with at least two **discovered carriers**, regardless of their old PASS/FAIL status.
- Optional `--min-independent-groups 2` makes the selection stricter but does **not** prove independent physical validation.
- Output is a *logical index/view*; consumer programs must use `ACTIVE_ATLAS_INDEX.json` to enforce it.
- Retains original provenance and topology admission counts in the source atlas. No source geometry or historical gate verdict is rewritten.

## Tests

```powershell
python -m unittest -v test_filter
```

Six portable regression tests (including correct preflight layout) passed in the build environment. This is not a claim of a completed run against your entire local atlas; the printed full counts come from the local `--dry-run`.
