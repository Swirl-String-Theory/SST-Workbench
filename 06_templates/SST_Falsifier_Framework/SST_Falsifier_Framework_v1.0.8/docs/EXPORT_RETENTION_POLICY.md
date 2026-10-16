# Run-unique exports and non-overwrite policy (v1.0.8)

- Stable pipeline work path: `Instance/<name>_<version>-outputs`.
- Existing work path is renamed to `...-outputs__<old-id>` **before** any new blind run. Existing legacy work tree: `...-outputs__LEGACY-<generated-id>`.
- `RUN_ID.json` anchors all phase filenames and is included in the output manifest.
- BLIND/REVEALED export names contain the same run ID; phases use distinct paths.
- `zipfile.ZipFile(mode="x")` forbids ZIP replacement; binary-exclusive `open("xb")` forbids PDF replacement.
- Instances are mutually excluded using an O_EXCL filesystem lock in the containing folder.
- Historical output snapshots are excluded from the current-run blinded source tree scan. The current `*-outputs` tree is still scanned.
- Do not change frozen protocol, numeric gates or source identifiers when rerunning.
- Recovery: If the active `-outputs` directory is partial after a failed run, leave it intact; the next new blind run archives it. A stale lock may be removed only after verifying no process is alive.
- **Migration:** no historical v1.0.7 reports or archives are renamed or deleted until the user executes v1.0.8 on that instance; even then, original contents are preserved by directory rename, and old PDF/ZIP files remain unchanged.
- **Limitation:** this policy prevents collisions between runs, not replacements of temporary checkpoints by a particular pipeline within one run.
