# A058 v0.1.3 Validation Record

Status: **PACKAGE_VALIDATED / READY_FOR_TARGET_RUN**  
Framework target: **SST Falsifier Framework v1.0.6 CANONICAL_FROZEN**

## Reason for v0.1.3

The v0.1.2 target run correctly reached Framework-v1.0.6 `FREEZE`, then failed because the instance archive omitted `private/REVEAL_NONCE.bin`. Inspection of the canonical framework generator (`tools/new_falsifier.py`) shows that every generated instance receives two 32-byte private files: `OPAQUE_ID_KEY.bin` and `REVEAL_NONCE.bin`. The same audit also found that the A058 report lacked the mandatory v1.0.6 report section markers, which would have been the next FREEZE failure.

v0.1.3 fixes both defects without changing the scientific parameter matrix, thresholds, checkpoint ladder, or geometry metrics.

## Canonical private-material invariant

Present and verified:

- `private/OPAQUE_ID_KEY.bin`: 32 bytes
- `private/REVEAL_NONCE.bin`: 32 bytes

`tools/check_private_material.py` is fail-closed and never regenerates either file. `run_pilot_all.cmd` and `run_freeze.cmd` invoke this preflight before FREEZE.

## Blindness hardening

Generated KnotPlot execution scripts contain construction commands and are therefore written under `private/campaign_scripts/<tier>/`. Raw KnotPlot stdout/stderr logs are written under `private/campaign_logs/<tier>/`. Public campaign manifests and numeric result paths contain anonymous topology/condition IDs only.

Pilot-generation validation:

- generated conditions: 150
- private `.kpc` scripts: 150
- public `campaign/scripts/`: absent
- forbidden-term hits in public pilot manifest: 0

## Exact Framework-v1.0.6 FREEZE-chain simulation

The exact canonical v1.0.6 implementations of `science_contract.py`, `report.py`, `source_registry.py`, `gates.py`, `blind.py`, `protocol.py`, `provenance.py`, and `util.py` were used against a disposable copy of this source tree after pilot generation.

Results:

```text
science_contract validation : []
source_contract validation  : []
gate_plan validation        : []
report validation           : []
blind-tree forbidden hits   : []
BLIND_TERMS commitment      : PASS
REVEAL commitment           : PASS
FREEZE                      : PASS
frozen protocol verification: PASS
protocol bundle SHA-256     : 1c549c02ad9f9aa6ec416dbe2d119dd21fd95271112d192f824fac6a0e7fc01e
```

The protocol-bundle hash is expected to reproduce for this exact v0.1.3 protocol byte set and shipped private material.

## Local source tests

```text
Python syntax compile : PASS (18 files)
instance-local tests  : 6 passed
private-material check: PASS
historical audit      : 50 scripts
pilot generator       : 150 conditions
```

## KnotPlot batch invocation

The runner invokes KnotPlot with `-stdin -nographics`. These are documented KnotPlot command-line options for standard-input scripting and windowless batch operation. The executable and working-directory resolver remain unchanged from v0.1.2.

## Release hygiene

The final release tree is cleaned of:

```text
.venv/
build/
__pycache__/
.pytest_cache/
*.pyc
*.pyd
*.dll
*.exe
*.lib
*.exp
*.obj
```

No generated campaign scripts, results, logs, commitment JSON files, or `FROZEN_PROTOCOL.json` are shipped. Those are created on the target machine in the preregistered order.
