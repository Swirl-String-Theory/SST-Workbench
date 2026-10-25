# A058-v0.3.8 — Native Scalar Export Closure

**Scope:** additive native scalar qualification for KnotPlot, on top of the exact v0.3.7 code. It does not modify the original A058-v0.2.9 scientific runner, registered 271 conditions, Framework v1.0.8 pin, historical blind commits, or any pre-existing native evidence.

## Install in your real A058-v0.3.2 workspace

Use the v0.3.8 **overlay** over the already reconciled v0.3.7 installation. Extract it **directly into the A058-v0.3.2 directory**, so `run_all.cmd` and `tools/scalar_export_closure.py` are side by side at the expected paths. No extra nested folder; do not replace or edit `KnotPlot.lnk`.

From that workspace, run:

```bat
run_all.cmd SELFTEST
run_all.cmd AUDIT_SCALAR_CLOSURE --source ".\A058_measurement_v037.zip" --out ".\A058_v038_history"
run_all.cmd RUN_SCALAR_CLOSURE --exe ".\KnotPlot.lnk" --dist ".\kpdist-23mar2025.zip" --out ".\A058_scalar_v038" --timeout 120
```

Both output paths must **not already exist**. The historical command is read-only and produces a four-case method audit. The native command generates 6 new runs: `dstep = 1,4` crossed with `go 32,128,512`. It starts KnotPlot through the original `.lnk` and respects its `Start in` workdir while exporting into the requested A058 output folder by absolute paths.

To inspect generated scripts before starting KnotPlot:

```bat
run_all.cmd GENERATE_SCALAR_CLOSURE --dist ".\kpdist-23mar2025.zip" --out ".\A058_scalar_staging_v038"
```

And then run the prepared, still-unused staging directory:

```bat
run_all.cmd RUN_SCALAR_CLOSURE --exe ".\KnotPlot.lnk" --out ".\A058_scalar_staging_v038" --timeout 120
```

Do not run `RUN_SCALAR_CLOSURE` a second time against a directory containing native log or output evidence; it deliberately fails closed.

## What qualifies numerically?

The exact native command order for each condition is `reset all; collision fast; load; ...; go N; final parameters; safe; data open; data format; data header; length; rog; data; data close; save ... ascii`. The *data initialization must follow the solver step and precede all scalar calculations*. Each condition independently checks:

- native process exit code and absence of fatal KnotPlot diagnostics;
- start and final positive `safe` markers **at sampled endpoints only**;
- `dstep` readback both before and after `go N`; iterator readback from `0` to exactly `N`; velocity/tangent/gravity/thermal force switches remain off;
- exactly one well-formed CSV measurement row with `Nbeads`, `Length`, `RoG`, `iteration`;
- independently recomputed closed-centerline length and gyration radius from that condition's ASCII XYZ snapshot, matched against the CSV within the explicitly registered v0.3.7 display tolerance;
- source seed and native script SHA-256 provenance.

`KP-alex.exe` and Alexander topology calculations are not required for this scalar contract. A numerical PASS does **not** establish a continuous collision-free path, convergence, topological invariant preservation between snapshots, hydrodynamical physics, or particle stability.

Exit codes: `0` = successful generation or all relevant method/scalar gates pass; `2` = correctly reported negative scientific/measurement qualification; `3` = operational or preflight error. No previous source artifacts are rewritten.

See `docs/SCALAR_EXPORT_CLOSURE_v0.3.8.md` and `evidence/2026_native_scalar_closure_v038/` for source-bound audit findings.

---

## Preserved v0.3.7 guide

# A058-v0.3.7 — Native Measurement Qualification

**Status:** ADDITIVE / LOCAL_VALIDATED / NATIVE_2026_NEW_DIAGNOSTIC_NOT_RUN / PHYSICS_UNRESOLVED.

Version v0.3.7 extends the already-working v0.3.6 A058 runner. It records why the existing `A058_probes3` / `A058_probes4` outputs are **numerically unqualified** even though KnotPlot returned exit code 0: real console and XYZ geometry versus a native CSV containing zeros, plus a failed `KP-alex.exe` helper.

This is a diagnostic experiment, not a modification to the original 271 registered blind slider campaign or to an SST claim.

From the source directory containing your original `KnotPlot.lnk` and `kpdist-23mar2025.zip`:

```bat
run_all.cmd SELFTEST
run_all.cmd QUALIFY_EXISTING --source ".\A058_probes4.zip" --out ".\A058_v037_q4"
run_all.cmd GENERATE_MEASUREMENTS --dist ".\kpdist-23mar2025.zip" --out ".\A058_v037_native"
run_all.cmd RUN_MEASUREMENTS --exe ".\KnotPlot.lnk" --out ".\A058_v037_native" --timeout 120
```

Or use `RUN_MEASUREMENTS --exe ".\KnotPlot.lnk" --dist ".\kpdist-23mar2025.zip" --out ".\A058_v037_fresh" --timeout 120` to generate the inputs only when the destination **does not yet exist**. A native negative result returns exit code 2 **after writing a qualification report**. Never overwrite the old evidence.

New protocol: 4 short real KnotPlot runs, `dstep` 1 or 4 with `data open` before or after `length`/`rog`, exact same 2025 trefoil seed and 32 `go` iterations. Native `parameters` readback is enclosed by markers. The original `KnotPlot.lnk` supplies EXE+working directory and is not modified. All exports use absolute A058 result paths.

For details and gate definitions see `docs/NATIVE_MEASUREMENT_QUALIFICATION.md`. See `CHANGELOG.md` and `VALIDATION.md` for evidence/limitations.

---

## Inherited historical notes

# A058-v0.3.5 — Relative Windows Shortcut Start-in Repair

**Status:** DEVELOPMENT / 38/38 local regressions PASS / native Windows KnotPlot NOT RUN in release environment. This is a launcher-only repair of A058-v0.3.3; blind gates and 271-condition registration remain unchanged.

The v0.3.3 resolver rejected every relative `WorkingDirectory` in the `.lnk` as `RuntimeError Shortcut WorkingDirectory is relative`. This version resolves the folder safely, preserving original KnotPlot resource lookup and absolute A058 probe I/O:

- Empty Start-in: use the target executable's own folder (recorded fallback).
- `.` or `./`: use the target executable's own folder (explicit behavior, not the current A058 folder).
- Another relative Start-in: evaluate both the EXE parent and the `.lnk` parent; choose only an unambiguous existing directory. If both differ, stop and request `--workdir`.
- Absolute Start-in: use that exact existing folder.
- Optional `--workdir "C:\absolute\KnotPlot-data"`: explicit override if Start-in is ambiguous or unavailable.

The `CHECK_SHORTCUT` command resolves the path without starting KnotPlot:

```bat
run_all.cmd CHECK_SHORTCUT --exe ".\KnotPlot.lnk"
run_all.cmd RUN_SAFE_PROBES --exe ".\KnotPlot.lnk" --out ".\A058_probes" --timeout 120
```

If resolution remains ambiguous, choose the real KnotPlot data folder explicitly:

```bat
run_all.cmd CHECK_SHORTCUT --exe ".\KnotPlot.lnk" --workdir "C:\full\path\to\KnotPlot"
run_all.cmd RUN_SAFE_PROBES --exe ".\KnotPlot.lnk" --workdir "C:\full\path\to\KnotPlot" --out ".\A058_probes" --timeout 120
```

The existing `probe.kpc` stays unchanged. A058 generates an explicit `probe.native.kpc` per condition: `load`, `data open`, `save` use absolute paths under `A058_probes/dstep_1` and `A058_probes/dstep_4`. KnotPlot's process cwd remains its normal data folder. Previous `FileNotFoundError` before launch does not require probe regeneration **if no native runtime files were created**; the runner refuses to overwrite any existing native results.

**Limits:** the provided `.lnk` was not available for real Windows COM testing. `CHECK_SHORTCUT` qualifies paths, not the KnotPlot runtime. Actual v2026 `-stdin -nographics`, getter, iteration and positive `safe` checks remain open. No claims of vortex physics or collision safety follow from these changes.

---

# A058-v0.3.3 — KnotPlot Shortcut / Working-Directory Hotfix

**Release scope:** surgical addition to A058-v0.3.2; still DEVELOPMENT / native Windows NOT_RUN.

The `--exe` option now accepts **the actual `.lnk` file**, and resolves its **Target**, **Start in / WorkingDirectory**, and optional **Arguments** with Windows PowerShell/WScript.Shell. The `.lnk` itself is never passed to CreateProcess (avoids WinError 193). For a direct `.exe`, the fallback CWD is its parent folder, *not* `A058_probes/dstep_*`.

**Important:** KnotPlot is launched with the correct original CWD, but the generated *runtime copy* `probe.native.kpc` contains **absolute paths** for `load A058_seed.kpf`, `data open A058_native_metrics.csv`, and `save A058_final.txt ascii`. Thus A058 exports remain under `A058_probes/dstep_1` and `dstep_4` rather than accidentally filling the KnotPlot installation folder. Original `probe.kpc` is immutable. Private launcher metadata is in `A058_probes/NATIVE_LAUNCH_PRIVATE.json`. A link with an empty **Start in** falls back to the executable directory, recorded explicitly; a malformed nonempty path stops safely.

From the A058-v0.3.3 folder containing the shortcut:

```bat
run_all.cmd SELFTEST
run_all.cmd RUN_SAFE_PROBES --exe ".\KnotPlot.lnk" --out ".\A058_probes" --timeout 120
```

`A058_probes` must have been created with `GENERATE_PROBES` and must not contain prior native results or logs; do not overwrite prior runs. If your existing v0.3.2 folder already contains generated probes, copy the hotfix's updated `tools/shortcut_runtime.py` and `tools/distribution_audit.py` there (or install the full release next to it) and run on that fresh probe folder. A shortcut containing nonempty Arguments is passed through verbatim as a Windows CreateProcess command line; the external KnotPlot build must still support appended `-stdin -nographics`.

**NOTE:** the hotfix does not yet certify numeric getters, the `go` iteration counter, or continuous collision safety. No native run was performed in the release environment.

---

# A058-v0.3.2 — KnotPlot Distribution-Assisted Parameter Audit

**Classification:** ADDITIVE / DEVELOPMENT / OFFLINE AUDIT VALIDATED, NATIVE KNOTPLOT UNVERIFIED.
**Inherited baseline:** A058-v0.3.1 repair coordinator, preserving A058-v0.3.0 clone and original A058-v0.2.9/v0.2.10 scientific code and historical results.
**Date:** 2026-10-21.

## Purpose

Audit the user-provided original `kpdist-23mar2025.zip` (KnotPlot distribution build 5093) for actual help/script evidence, independently read 1.0 single-component KnotPlot binary geometries, and generate safe, opt-in dstep comparison scripts. The archive contains utility C/C++ source but *not the complete KnotPlot dynamics solver*. It is **not** repackaged or redistributed with this release. References to its internal files are recorded by relative path and SHA-256.

## Requirements

- Python 3.10+ (no third-party dependencies for v0.3.2 audit tools).
- The user-supplied, unchanged `kpdist-23mar2025.zip` on your computer.
- The existing A058-v0.3.0 on Windows only if using the inherited v0.3.1 `--legacy` repair functions.
- A real Windows KnotPlot executable **only** for optional native probes; this package has none.

## Offline auditable commands — from this extracted release directory

```bat
run_all.cmd SELFTEST
run_all.cmd AUDIT_ALL --dist "C:\path\to\kpdist-23mar2025.zip" --out "C:\path\to\NEW_A058_distribution_audit"
run_all.cmd KPF_AUDIT --dist "C:\path\to\kpdist-23mar2025.zip" --out "C:\path\to\NEW_A058_kpf_audit"
run_all.cmd GENERATE_PROBES --dist "C:\path\to\kpdist-23mar2025.zip" --out "C:\path\to\NEW_A058_safe_probes"
```

Each `--out` directory **must not exist**. Static audit outputs: `SOURCE_EVIDENCE.json`, `GUI_CONTROL_MATRIX.json`, `KPF_AUDIT.json`, `KPF_AUDIT.csv`, and `RUN_RECEIPT.json`. KPF audit covers `basic/0_1`, `3.1`, `4.1`, `8.19`, and the multicomponent `6.3.3` as a mandatory **unsupported scope** test; no topological knot certification is implied.

## Optional native test (explicit user action only)

```bat
run_all.cmd RUN_SAFE_PROBES --exe "C:\path\to\KnotPlot.exe" --out "C:\path\to\NEW_A058_safe_probes" --timeout 120
```

Runs two independent 32-iteration processes with `dstep = 1` and `dstep = 4`, each from the exact same KPF bytes and `collision fast`. The generated scripts explicitly turn OFF velocity-proportional force (`velforce`), buggy tangential force (`tanf`), gravity (`grav`), and thermal agitation (`therm`); enable `elec`, `mech`; disable `amech`. It records `safe`, `length`, `rog`, `alex -1`, `data format` and an ASCII export. Raw `NATIVE_STDOUT_PRIVATE.log` is **PRIVATE** and may contain local path/parameter data. Native command syntax, successful 3D export and the `safe` check **must** be verified against the user's newer KnotPlot build; unsupported tokens are reported as unsupported, not interpreted as physics. Output is never overwritten. A `dstep` negative-control pass does not certify no crossings *between* checkpoints.

Do **not** run the archived `relaxA-bm.kps` and `relaxB-bm.kps` unchanged for scientific controls: both contain `coll a`, permitting collisions, and `go 9999999`. The v0.3.2 probes are new, short, safer adaptations, not replications of their original execution outcomes.

## Inherited v0.3.1 diagnostics

```bat
run_all.cmd DIAGNOSE --legacy "C:\path\to\A058-v0.3.0"
run_all.cmd AUDIT_CONTROLS --legacy "C:\path\to\A058-v0.3.0"
```

The source-engine/framework locator fix, native PRIVATE logs and old 271-condition frozen protocol preservation are unchanged. No automatic old-gate reinterpretation, reveal, new blind freeze, geometry mutation or A058 private mapping is performed. Scientific changes to force models require a separately preregistered version.

## Evidence labels

- `SOURCE_OBSERVED`: exact documentation/script content in 2025 distribution.
- `KPF_PARSED`: centerline coordinates obtained independently from 2025 catalog binary.
- `RUNTIME_UNVERIFIED`: no actual 2026 KnotPlot execution in this environment.
- `UNSUPPORTED_LINK_OR_ENCODING`: intentional scope restriction, not model falsification.
- `NUMERICAL_CONTROL_ONLY`: `dstep`, `max-dr`, and collision-guard studies do not establish Euler/vortex dynamics.

See `docs/DISTRIBUTION_AUDIT.md`, `docs/CONTROL_MATRIX.md`, and `VALIDATION.md`.


## v0.3.5: Windows shortcut %ENVVAR% correction

A `.lnk` may contain `Start in: %SST-Workbench%\01_research\...\A058-v0.3.2`.
The previous v0.3.4 runner incorrectly attempted to treat that string as a
plain relative path. v0.3.5 first expands Windows `%VAR%` placeholders. If a
variable is unavailable to Python, it may be resolved from a uniquely named
ancestor directory of the shortcut itself. Unmatched placeholders fail closed.

**The shortcut target and shortcut file are never modified.**
The KnotPlot process inherits the resolved `Start in` directory, and the
KnotPlot script references per-probe inputs/outputs by explicit absolute paths
under `A058_probes/`. This is independent of the executable install folder.

Preflight and run without changing the existing .lnk:

```bat
run_all.cmd CHECK_SHORTCUT --exe ".\KnotPlot.lnk"
run_all.cmd RUN_SAFE_PROBES --exe ".\KnotPlot.lnk" --out ".\A058_probes" --timeout 120
```

If older attempted launches have created native output/log files, use a NEW
output directory to prevent overwriting committed evidence. This fix remains
locally tested only; final qualification requires the native Windows run.


## v0.3.6 — generated seed preflight

`CHECK_PROBES --out <path>` is read-only; for a new path `RUN_SAFE_PROBES --exe ".\KnotPlot.lnk" --dist ".\kpdist-23mar2025.zip" --out ".\A058_probes_NEW" --timeout 120` creates its inputs exactly once. The old missing `A058_seed.kpf` exception is identified **before** launching KnotPlot. Do not reuse a partial/native-run output folder. See `docs/PROBE_INPUT_PREFLIGHT_v0.3.6.md`.
