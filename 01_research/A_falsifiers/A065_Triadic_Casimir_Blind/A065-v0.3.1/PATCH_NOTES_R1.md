# A065 v0.3.1-r1 - framework installation hardening

**Maintenance-only release.** No changes to the original three data seals, original 300-node centerline, numerical protocol, tolerances, physics kernels, registered gate questions, or reveal restrictions.

## Fixed defects from Windows 14 October 2026 run audit

1. **WinError 183 native directory collision**: canonical v1.0.7 `new_falsifier.py` already creates `native/` and `preregistration/`. Instead of `shutil.copytree` into an existing directory, `framework_bridge.install._merge_additive` now recursively copies only missing instance files, checks SHA-256 on identical existing files, and rejects mismatched collisions without overwriting canonical scaffold material.
2. **False success of ALL**: after the portable report and PDF have been written, `ALL`, `FRAMEWORK`, `FULL` and `BASIC` exit with code 3 if the official framework did not complete, including when the framework is missing. The framework status is also written to `FRAMEWORK_STATUS.json` and exported inside blind evidence.
3. **DYNAMICS stdout-only**: `DYNAMICS` now writes `outputs/DYNAMICS_RESULT.json` in the unique run workspace with simulation scope and provider commitment, and publishes `<RUN_ID>_DYNAMICS_RESULT.json` individually, as well as within the `BLIND_RESULTS.zip`, all with create-only semantics and export SHA-256.

## Explicitly unchanged

- Preregistered `N=75/150/300`, fixed `epsilon=0.12`, `Gamma=1`, final time `T=0.04`, 5% tolerance.
- Original G2 numerical failures and physical G3 `UNRESOLVED` / reveal withheld.
- Framework v1.0.7 stays external, unmodified and pinned; new instance gets a separate prefreeze scientific contract.
- Three seals and all source data are byte-identical to public A065 v0.3.1.
- Independent Fremlin source remains raw-hash/parser-only, not a dynamically qualified provider.

## Windows

Unpack *beside* v0.3.1 under A065-v0.3.1-r1 and run:

```cmd
run_all.cmd FRAMEWORK
run_all.cmd ALL
run_all.cmd DYNAMICS
```

Exports: `exports/<RUN_ID>/*`, historical runs untouched. Portable LaTeX report is self-contained, compiled with pdflatex when available; framework's official PDF requires native LaTeX.

## Regression and scope

`run_all.cmd SELFTEST` runs original tests plus r1 collision, failure propagation and DYNAMICS JSON checks. The genuine Windows framework run cannot be certified in the Linux test environment and must be verified on the user's installed framework.
