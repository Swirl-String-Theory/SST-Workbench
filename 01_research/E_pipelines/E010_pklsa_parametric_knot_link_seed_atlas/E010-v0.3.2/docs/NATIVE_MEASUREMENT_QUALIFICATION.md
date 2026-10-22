# A058-v0.3.7 — Native Measurement Qualification

## Scope, provenance, evidence

This is a **diagnostic addendum** to the A058-v0.3.6 runner. It does **not** change the 271 registered anonymous-slider experiments or unlock previously failed frozen science gates. All old gates and blind commitments must be assessed from the authentic original engine, independently of this tool.

The source evidence comprises the user-provided `A058_probes3.zip`, `A058_probes4.zip`, `kpdist-23mar2025.zip` and the v0.3.6 launcher. The executable in the received native logs identifies itself as October 18, 2026 (separate from the March 23, 2025 static distribution).

## Original native failures, observed from two archives

Each archive contains two independent `go 32` runs from the same 47-bead `basic/3.1` seed. The two dstep exported centerlines are byte-identical in each archive. The native console prints `tot 56.757945` and `rog 4.355587`, consistent with independent XYZ measurement (approximately 56.75794537, 4.35558697). However native `/N,/l,/g,/D,/I` CSV contains `47,0,0,0,32`. The log states `can't open file KP-alex.exe`. Thus:

| Gate | Native evidence | Verdict |
|---|---|---|
| Process 0 exit code | Yes | Native process completed |
| Start/final `safe` console | Positive in both snapshots | Snapshot-only observation |
| `/I` iteration counter | 32 | Recorded by KnotPlot data export; not independent solver time |
| Native CSV length and RoG | 0 / 0 | FAIL against XYZ and console |
| Alexander determinant `/D` | helper `KP-alex.exe` cannot open | UNAVAILABLE, no knot determinant claim |
| dstep getter readback | Not in original scripts | UNRESOLVED |
| Independent physics or convergence | Not supplied | UNRESOLVED |

Exit status zero **does not qualify a data field**. Public receipt contains hashes; native stdout should be kept private because it includes local machine paths.

## Protocol of NEW diagnostic experiment (four conditions)

The *same* `basic/3.1` KPF seed from `kpdist-23mar2025.zip` is used for all runs. Four conditions cover `dstep` in {1, 4} crossed with two file-operation orderings:

- `before`: `data open` + `data format` + `data header`, then `length`, `rog`, `data`.
- `after`: `length`, `rog`, then `data open` + `data format` + `data header` + `data`.

Each independent KnotPlot process uses `reset all`, `collision fast`, `elec=on`, `mech=on`, `amech=off`, `velforce=off`, `tanf=off`, `grav=off`, `therm=off`, a single `go 32`, two bounded `safe` checks, and a bounded `parameters` dump following parameter assignment. `alex -1` and `/D` are **excluded from core numerical CSV qualification** to isolate the known external-helper failure. `KP-alex.exe` is separately checked for presence at the executable folder, shortcut Start-in and PATH; presence is NOT evidence it works. No helper is downloaded or copied into the project.

The original `.lnk` is preserved. The launcher resolves `%SST-Workbench%` in `Start in` and passes this value as process cwd. The generated `probe.native.kpc` references each seed, CSV and XYZ by **absolute paths** under the new A058 diagnostic folder. Original `probe.kpc` scripts are never rewritten.

## Gates and statuses

- **Geometry**: finite three-column XYZ, ≥3 beads; curve length and gyration independently recomputed from coordinates.
- **Console agreement**: parse native `#0: Nb … tot …` and stand-alone `rog` output; check against XYZ within 2e-5 absolute or 1e-6 relative (KnotPlot native-unit numbers).
- **CSV agreement**: `/N`, `/l`, `/g`, `/I` must be readable numeric values (no NaN/Inf), matching XYZ for bead count/length/Rg, and `/I == 32`. Zero scalar values with nonzero XYZ must fail.
- **Runtime flags**: exact `dstep` command in script, `collision fast`, velocity/tangential/grav/thermal force exclusion; actual `dstep` getter must appear between `A058_READBACK_BEGIN` and `A058_READBACK_END` and equal requested value to six-display-decimal tolerance.
- **Safety**: two positive, bounded console `Current position is safe.` messages. This establishes only **the two snapshots**, not continuous stepwise collision exclusion.
- **Alex**: missing helper independently classified as unavailable; optional physics/topology not promoted.

`QUALIFIED_NUMERICAL_MEASUREMENT_ONLY` requires every applicable gate; a native process that exits successfully with zero `/l` or `/g` is `FAIL_MEASUREMENT_QUALIFICATION`. Missing getter is `INCOMPLETE_PARAMETER_READBACK` when remaining checks are valid. Native status cannot establish long-time attractors, Euler closure, or vortex physics.

## Windows usage

The input distribution, `KnotPlot.lnk`, and all original `A058_probes3`, `A058_probes4` are kept unchanged. Examples from a folder containing your shortcut and distribution:

```bat
run_all.cmd SELFTEST
run_all.cmd QUALIFY_EXISTING --source ".\A058_probes4.zip" --out ".\A058_v037_legacy_qualification4"
run_all.cmd GENERATE_MEASUREMENTS --dist ".\kpdist-23mar2025.zip" --out ".\A058_measurement_v037"
run_all.cmd RUN_MEASUREMENTS --exe ".\KnotPlot.lnk" --out ".\A058_measurement_v037" --timeout 120
```

Or one-step generation and execution into a **new, nonexisting** directory:

```bat
run_all.cmd RUN_MEASUREMENTS --exe ".\KnotPlot.lnk" --dist ".\kpdist-23mar2025.zip" --out ".\A058_measurement_v037_NEW" --timeout 120
```

**Exit codes:** 0 = generation success or all numerical measurements qualified; 2 = negative/incomplete qualification receipt written; 3 = failure before a valid result could be produced. Exit 2 is not a KnotPlot process crash. Do not retry within a partially populated output directory: choose a new one to protect raw evidence.

### Files

`MEASUREMENT_DESIGN.json`, each condition's `probe.kpc`, `probe.native.kpc`, `NATIVE_STDOUT_PRIVATE.log`, `A058_final.txt`, `A058_native_metrics.csv`, `NATIVE_LAUNCH_PRIVATE.json`, `NATIVE_RESULTS.json`, and `qualification/{QUALIFICATION.json,MEASUREMENT_MATRIX.csv,QUALIFICATION.md}`. New `probe.native.kpc` and raw logs may expose local paths and remain **private**. No secret A058 axis mapping or private blind keys are included.
