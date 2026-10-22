# A058 v0.3.6 — Native probe input preflight

**Classification:** engineering maintenance, not a new scientific experiment.

## Verified root cause for the reported 2026-10-22 log

The shortcut resolved successfully to `C:\Program Files (x86)\KnotPlot\KnotPlot.exe` and the A058 v0.3.2 `Start in` directory. The later `FileNotFoundError: A058_probes\\dstep_1\\A058_seed.kpf` originated from Python `run_safe_probes` preflight (`read_bytes()` of a generated seed), **before native KnotPlot was started**. The log proves that the expected input file was missing at the time of that attempt; it does not establish how it went missing. Neither a KnotPlot failure nor a result of a physics falsifier may be inferred.

`FileExistsError: Previous native probe evidence present` in an earlier attempt correctly signalled the prohibition on overwriting previous evidence. Deleting old outputs is not a safe method of resetting a run. Use a new directory.

## New commands

Run these from the A058 project directory (no changes to KnotPlot.lnk):

```bat
run_all.cmd CHECK_SHORTCUT --exe ".\\KnotPlot.lnk"
run_all.cmd CHECK_PROBES --out ".\\A058_probes"
```

`CHECK_PROBES` returns one of `NOT_GENERATED`, `INVALID_MANIFEST`, `INCOMPLETE_OR_MODIFIED`, `PREVIOUS_NATIVE_ATTEMPT_PRESENT`, or `READY`, together with missing paths, hash mismatches, and existing native evidence. It never launches KnotPlot or alters the directory. It exits nonzero if not READY.

### Existing runner: two-step safe procedure

```bat
run_all.cmd GENERATE_PROBES --dist ".\\kpdist-23mar2025.zip" --out ".\\A058_probes_NEW"
run_all.cmd CHECK_PROBES --out ".\\A058_probes_NEW" --dist ".\\kpdist-23mar2025.zip"
run_all.cmd RUN_SAFE_PROBES --exe ".\\KnotPlot.lnk" --out ".\\A058_probes_NEW" --timeout 120
```

Choose a directory name that does not yet exist.

### New one-command safe procedure

```bat
run_all.cmd RUN_SAFE_PROBES --exe ".\\KnotPlot.lnk" --dist ".\\kpdist-23mar2025.zip" --out ".\\A058_probes_NEW" --timeout 120
```

**Only if** `--out` is absent does the runner generate the two probe input sets from the supplied distribution. Existing or partially generated directories are never auto-repaired or overwritten. The original `probe.kpc` is authenticated against the generator, both `A058_seed.kpf` files are SHA-checked, and `--dist` (when provided) must match the original distribution hash. Native `probe.native.kpc` rebinding preserves the `.lnk` Start-in and writes all outputs explicitly inside the new A058 probe directory.

## Boundaries

- Uses the existing two 32-step `dstep=1/4` Damped probes, `collision fast`, excludes `velforce` and `tanf` from this branch.
- Original 271-condition blind science protocol and existing gate ledger are unchanged.
- Native runtime getter, real iteration count, positive safety checks, and continuous no-self-intersection/topology preservation are **NOT certified by this patch**.
- The tests do not execute actual Windows KnotPlot.exe; passing Python mocks cannot certify its behavior.
