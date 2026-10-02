# SST v0.3.3 continuum ladder runner

Place these files in the root of:

`SST_ideal_links_comprehensive_test_suite_v0.3.3`

so that the resulting paths are:

- `run_continuum_ladder.cmd`
- `scripts/run_continuum_ladder.py`

The launcher uses the active project `.venv` when available, executes the existing
`run_native_preflight.py` once, and then runs the v0.3.3 continuum audit with the
native backend.

## Default adaptive ladder

Double-click or run:

```cmd
run_continuum_ladder.cmd
```

Default links:

`L6a4 L4a1 L6n1 L7n2`

The adaptive ladder is:

1. `[128, 256, 512]`, tolerance 3%
2. only failed links -> `[192, 384, 768]`, tolerance 2%
3. only failed links -> `[256, 512, 1024]`, tolerance 1.5%

A link that passes is not recalculated at higher resolution.

## Exact equivalent of the requested max run

```cmd
run_continuum_ladder.cmd max
```

This performs the same v0.3.3 continuum resolution set as:

```powershell
.\run_continuum.ps1 -Preset max -Ids L6a4,L4a1,L6n1,L7n2
```

with the same max config baseline `[128,256,512]` and 3% tolerance.

## Direct ultra run

```cmd
run_continuum_ladder.cmd ultra
```

This directly uses `[256,512,1024]` with a 1.5% tolerance.

## Outputs

A timestamped folder is created containing:

- each stage's original `continuum_summary.csv`;
- each stage's per-link JSON files;
- `config_used.json`;
- `continuum_ladder_all_stages.csv`;
- `continuum_ladder_final.csv`;
- `continuum_ladder_metadata.json`.

`NOT_CONVERGED_AT_MAX_LADDER` is not treated as a program failure; it is retained
as a numerical result.
