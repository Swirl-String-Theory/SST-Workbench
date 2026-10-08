# A054 v0.2.0-r2 native runner restore v2

This package restores exactly the native extension expected by the sealed
A054 campaign `full_20261006_230912`.

Expected SHA-256:

`ba6f8c9fdbcaa2525a4268d597c697c9067a331a170bd63a04b4440d640b2645`

The tool auto-discovers `SST-Workbench`, so it can be run from any folder.

Recommended:

```bat
restore_and_verify.cmd
```

If auto-discovery fails:

```bat
restore_and_verify.cmd --workbench-root C:\workspace\projects\SST-Workbench
```

The tool:
- verifies the payload hash;
- verifies every other RUNNER_MANIFEST-tracked source before touching the binary;
- backs up the current `_native.pyd`;
- performs an atomic replacement;
- verifies the complete runner manifest after replacement;
- on Windows imports `a054_blind._native` from the exact sealed runner path;
- reports `backend_name()` and OpenMP state.

Do not rerun A055 until this tool prints `"status": "PASS"`.
