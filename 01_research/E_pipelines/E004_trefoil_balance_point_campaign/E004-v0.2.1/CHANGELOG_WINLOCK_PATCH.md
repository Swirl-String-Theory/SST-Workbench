# Trefoil Balance Point Campaign v0.2.1 — Windows directory-lock runtime patch

Scientific design unchanged.

Fixes `PermissionError: [WinError 5] Access is denied: ...\\kpc_standard` caused by
`generate_kpc.py` deleting and recreating the complete generated-script directory.

The patch:

- leaves the preregistered `generate_kpc.py` unchanged;
- leaves `balance_design.json`, q/h/p values, checkpoints, analysis and gates unchanged;
- preserves the existing `PREREGISTRATION_LOCK.json` validity;
- changes `run_05_generate.cmd` to call `generate_kpc_safe.py`;
- overwrites the 20 expected KPC files and `index.json` in-place instead of using `shutil.rmtree()`.
