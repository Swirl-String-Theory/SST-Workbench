---
name: fseries outdir nest
overview: "Nest campaign outputs under out/fseries/, out/knotplot/, and out/ideal/; batch default resolutions become the triple 300,600,900 with -t12."
todos:
  - id: outdir-prefixes
    content: "Default bases: out/fseries/<stem>, out/knotplot/<label>/g…, out/ideal/<sid>"
    status: pending
  - id: batch-defaults
    content: "run_catalog_batch: out/fseries paths + --outdir to children; DEFAULT_RESOLUTIONS=300,600,900"
    status: pending
  - id: tests-docs
    content: Update tests/README for three out/ trees + triple; full unittest suite green
    status: pending
isProject: false
---

# Nested outdirs + batch triple 300/600/900

## Goal

Default campaign roots (then existing `tN` / `r_*` via [`resolve_outdir`](c:\workspace\projects\SST-Workbench\KnotPlot\ridgerunner\run_ideal_knot.py)):

| Source | Today | New default |
|--------|-------|-------------|
| Fourier fseries | `out/3_1/t12/` | **`out/fseries/3_1/t12/`** |
| KnotPlot knot/link/torus | `out/K3.1/g1k/t12/` | **`out/knotplot/K3.1/g1k/t12/`** |
| Gilbert ideal | `out/3_1_1/t1/` | **`out/ideal/3_1_1/t1/`** |

Batch summary: **`out/fseries/batch_fseries_summary.json`**.

Batch default resolutions: **`300,600,900`** (triple). Threads default **12** unchanged.

```bat
run_catalog_batch.cmd --all-fseries
rem → out\fseries\<stem>\t12\  with -r300,600,900 -t12

run_catalog_knot.cmd --knot3.1 -t8
rem → out\knotplot\K3.1\g1k\t8\

run_ideal_knot.cmd --3:1:1
rem → out\ideal\3_1_1\t1\
```

Explicit `--outdir` still wins (no extra prefix).

Gilbert ideal **resolutions** default stays `300,600,1200` (only outdir nest changes for ideal).

## Changes

### 1. [`run_catalog_knot.py`](c:\workspace\projects\SST-Workbench\KnotPlot\ridgerunner\run_catalog_knot.py)

```python
# knotplot
base_outdir = args.outdir or (
    BUNDLE / "out" / "knotplot" / label / go_subdir(go_tag)
)
# fseries
base_outdir = args.outdir or (BUNDLE / "out" / "fseries" / stem)
```

Align catalog `--resolutions` default to **`300,600,900`** (same triple as batch).

### 2. [`run_ideal_knot.py`](c:\workspace\projects\SST-Workbench\KnotPlot\ridgerunner\run_ideal_knot.py)

```python
base_outdir = args.outdir or (BUNDLE / "out" / "ideal" / sid)
```

### 3. [`run_catalog_batch.py`](c:\workspace\projects\SST-Workbench\KnotPlot\ridgerunner\run_catalog_batch.py)

- `DEFAULT_RESOLUTIONS = "300,600,900"`
- Summary under `out/fseries/`
- Child paths / dry-run: `out/fseries/<stem>/t{threads}`
- Pass `--outdir` = `out/fseries/<stem>` into each `catalog_main` call

### 4. Docs + tests

- README tables/examples for `out/fseries/`, `out/knotplot/`, `out/ideal/`
- Update unit tests that hardcode `out/3_1_1`, `out/K3.1`, batch outdir assumptions, default resolution lists
- Full suite green (incl. `test_run_ideal_knot`, `test_run_catalog_knot`, `test_run_catalog_batch`)

## Verification

```bat
python -m unittest test_run_ideal_knot.py test_run_catalog_knot.py test_run_catalog_batch.py … -v
run_catalog_batch.cmd --stems 3_1 --dry-run
```

Dry-run: `out\fseries\3_1\t12` and resolutions `[300, 600, 900]`.
