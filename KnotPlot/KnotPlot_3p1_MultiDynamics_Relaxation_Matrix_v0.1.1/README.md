# KnotPlot 3.1 Multi-Dynamics Relaxation Matrix — patch v0.1.2

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
