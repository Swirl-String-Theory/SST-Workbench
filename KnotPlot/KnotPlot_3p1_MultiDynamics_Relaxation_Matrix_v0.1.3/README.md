# KnotPlot 3.1 Multi-Dynamics Relaxation Matrix v0.1.4

## v0.1.4 critical runtime fix

The discovery scripts are now version-independent. Do **not** edit output paths
when renaming the workmap. The runner renders `runtime_scripts/*.kpc` for the
current directory and validates output creation there.

Before the matrix, the runner automatically:
1. tests `load 3.1`;
2. tests `save` + `coords` into the current workmap;
3. probes `nbeads 300` and `refine nbeads 300`;
4. selects the syntax accepted by the installed KnotPlot.

On failure inspect `preflight/` and `logs/*_audit.json`.

Recommended:

```bat
run_static_audit.cmd
run_fresh_discovery.cmd
```

---

## v0.1.3 Windows launcher hotfix

A packaging bug in v0.1.2 wrote literal `\r\n` text into six new `.cmd` launchers. v0.1.3 rewrites them with real Windows CRLF line endings. Verify the installation with:

```bat
run_cmd_lineending_audit.cmd
run_static_audit.cmd
```

The first command should end in `CMD LINE-ENDING AUDIT PASS`; the second should now actually execute `kpc_audit.py`.

## Intended architecture

This workbench has two deliberately separated scientific phases:

1. **DISCOVERY on trefoil 3.1** — vary one KnotPlot preparation variable/family at a time and measure how the generated geometry changes.
2. **CATALOG propagation** — only after a recipe has been selected/approved, regenerate all catalog build scripts with that exact recipe and run them.

The matrix is therefore **not** evidence that a KnotPlot-low-energy state is physically stable. It is a controlled candidate generator for downstream Euler / finite-core / Floquet falsifiers.

## Why this patch was needed

The included `out/` and `logs/` are from an older run in which the target KnotPlot executable reported `unknown command` for `charge`, `hooke`, `power`, and `timeincr`, and reported `nbeads` obsolete. Those results must not be reused as a valid variable-effect campaign. The current KPC source already uses command syntax such as `charge 15`; v0.1.2 additionally switches the target runtime to `refine nbeads N`, removes the unavailable `alex -1` helper call, and makes the runner fail on such log errors.

## Recommended fresh discovery

```bat
run_fresh_discovery.cmd
```

This archives the old `out/`, `logs/`, and `analysis/`, runs a static KPC audit, executes all ten matrix families, validates every expected `save` + `coords` file, then writes:

- `analysis/matrix_metrics.csv`
- `analysis/matrix_analysis.json`
- `analysis/MATRIX_EFFECTS.md`

A sweep whose final XYZ files are all byte-identical is flagged automatically.

## Recipe selection

`catalog_recipe.json` starts deliberately with:

```json
"approved_for_catalog": false
```

Seed it from a matrix candidate, for example:

```bat
python select_catalog_recipe.py --candidate C22_ME_q15p0
```

After the geometry/downstream-stability evidence justifies it:

```bat
python select_catalog_recipe.py --candidate C22_ME_q15p0 --approve --reason "selected after matrix + downstream stability gates"
```

You can then edit `catalog_recipe.json` if the final recipe combines knowledge from several sweeps rather than copying one tested candidate.

## Prepare and run catalog

```bat
run_prepare_catalog.cmd
run_catalog_one.cmd knot_3.1
run_catalog.cmd
```

`run_prepare_catalog.cmd` regenerates the 49 catalog scripts from the source `KnotPlot/knots` tree and injects the approved recipe. Every generated script carries `RECIPE_ID` and `RECIPE_SHA256`. `run_catalog.cmd` refuses stale or unapproved scripts.

`97_run_catalog.kpc` remains an interactive include master, but the recommended Windows batch route is `run_catalog.cmd`, which runs one catalog item per KnotPlot process and validates outputs.

## Important separation

`run_all.cmd` means **all discovery matrix families**, not “matrix + catalog”. The catalog is intentionally gated behind explicit recipe approval.
