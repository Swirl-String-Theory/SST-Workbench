# KnotPlot 3.1 Trefoil Seed Campaign v0.1.3


## Critical v0.1.3 syntax correction

Production KPC generation now uses only command forms directly observed in the
user's working `build_knot_0.1.kpc` or confirmed by the target KnotPlot logs.

Before relaxation, run:

```bat
run_16_validate_kpc_syntax.cmd
```

It rejects obsolete/unknown commands before a long campaign is allowed to run.


## v0.1.2 output-directory hotfix

The target Windows run showed that KnotPlot could load and execute the base
script, but failed to open the requested output files because empty runtime
directories such as `base\` were not present after ZIP extraction.

v0.1.2 fixes this in two independent ways:

- `run_campaign.py` creates the parent directory of every parsed `save` and
  `coords` target before launching KnotPlot.
- Runtime folders contain `.keep` placeholders so normal ZIP extraction also
  creates them.

This is a pure file-system/runtime fix. The frozen 38-seed manifest,
perturbation amplitudes/modes, topology-safety definitions and fixed relaxation
protocol are unchanged.


## v0.1.1 target-runtime hotfix

The first real Windows run established that `load 3.1` is not the failure.
The campaign stopped because `alex -1` requires the external helper
`KP-alex.exe`, which is absent on the target installation.

v0.1.1 therefore:

- removes `alex -1` from base and production checkpoints;
- keeps `safe`, `dowker`, and `lnknum`;
- treats KnotPlot's pre-banner `nothing loaded / nothing to save / nothing to
  output` text as startup noise when the requested output files are actually
  written;
- still fails on missing files, `unknown command`, obsolete/rejected syntax,
  or genuine file-open errors.

The 38 frozen seed definitions and all relaxation parameters are unchanged.
The failed v0.1.0 base-export run produced no production geometry, so v0.1.1
remains prospective with respect to the intended seed campaign.

Prospective initial-condition campaign for generating genuinely new relaxed
trefoil geometries before the SST Phase-Feedback Delay v0.2 confirmatory test.

The key design change is **seed diversity with one fixed relaxation protocol**.
It does not repeat the old strategy of many force labels applied to essentially
one start geometry.

## Expected location

Place the extracted folder under the KnotPlot workspace, for example:

```text
C:\workspace\projects\SST-Workbench\KnotPlot\
    KnotPlot.lnk
    KnotPlot_3p1_Trefoil_Seed_Campaign_v0.1.1\
```

`run_campaign.py` resolves the sibling `KnotPlot.lnk`. You can override it with
the environment variable `KNOTPLOT_LNK`.

## Full run

```bat
run_all.cmd
```

Stages:

```text
run_00_install.cmd
run_03_selftest.cmd
run_02_verify_preregistration.cmd
run_05_export_base.cmd
run_10_generate_seeds.cmd
run_15_generate_kpc.cmd
run_20_relax.cmd
run_30_analyze.cmd
run_40_pack_outputs.cmd
```

The base stage uses the installed KnotPlot itself:

```text
reset all
load 3.1
refine nbeads 300
centre
fitto mindist 1.05
coords .../base/base_3p1_300.txt
```

KnotPlot's `coords` output is intentionally used because KnotPlot can directly
`load` that ASCII coordinate format again.

## Production output

The phase-delay falsifier can consume:

```text
...\KnotPlot_3p1_Trefoil_Seed_Campaign_v0.1.1\out
```

with files such as:

```text
S001_bishop_helical_i00000.txt
S001_bishop_helical_i01000.txt
S001_bishop_helical_i04000.txt
S001_bishop_helical_i10000.txt
```

After the campaign, `analysis\REPORT.md` reports exact endpoint uniqueness and
novelty against the frozen 10-geometry v0.1.7 registry.

If it reports at least 8 novel unique endpoints, preview the folder with your
Phase-Delay v0.2.x falsifier and only then run its confirmatory chain.
