# A065-v0.3.0 / official frozen framework handoff

The package uses the installed **CANONICAL_FROZEN SST Falsifier Framework v1.0.7** original `tools/new_falsifier.py`, `run_instance.py`, protocol freeze, blind gate ledger and reveal policy. **No framework source is vendored or edited.**

The framework instance ID is `A065`, version `v0.3.0`, profile **cpu**, and `pdf_required=true`. Both `FRAMEWORK` and `FULL` modes exit nonzero if the required framework PDF fails; `ALL` always generates an additional portable fallback PDF.

A local smoke test with the available v1.0.7 source subset (not the user's complete Windows installation) executed `FREEZE`, `FULL`, `REVEAL_IF_ALLOWED`, produced its own 5-page LaTeX PDF and gate ledger:

```
G0 PASS
G1 PASS
G2 FAIL                  D01 spatial 75/150: 8.729% > 5%
G3 NOT_RUN_PREREQUISITE
G4 NOT_RUN_PREREQUISITE
G5 NOT_RUN_PREREQUISITE
G6 NOT_APPLICABLE
G7 NOT_APPLICABLE
G8 NOT_RUN_PREREQUISITE
G9 DEFERRED
```

The full installed framework must be run on the target Workbench before interpreting native CPU certification. Local independent GCC binary64 numerical parity does not satisfy physical G5. Fremlin candidate registered from E010, raw geometry not bundled; G4 cannot be passed via labels or numerical subsampling. Three SHA256-sealed datasets survive unchanged in the framework instance.
