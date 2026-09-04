# Path resolution (SP01)

Central resolution for Workbench roots and shared datasets. Prefer these helpers
over `Path(__file__).parents[N]` or hardcoded absolute paths.

## Python — `07_scripts/sst_workbench_paths`

```python
import sys
from pathlib import Path

# Until scripts/ is moved to 07_scripts (SP04), add the package parent:
sys.path.insert(0, str(Path(".../SST-Workbench/07_scripts")))

import sst_workbench_paths as swp

root = swp.WORKBENCH_ROOT          # or swp.workbench_root()
data = swp.DATA_ROOT
knots = swp.KNOT_DATASET           # KnotPlot/knots/final until SP07 moves it
ideal = swp.IDEAL_SOURCES
family = swp.resolve_family("A042")
vdir = swp.resolve_family("A006", version="v0.2.0")
```

### Resolution order

For each variable: **explicit argument → environment variable → upward marker
search → packaged default**.

| Variable | Env | Default (after moves) | Live fallback (pre-move) |
|----------|-----|------------------------|---------------------------|
| `WORKBENCH_ROOT` | `SST_WORKBENCH_ROOT` | dir containing `.sst-workbench-root` | — |
| `DATA_ROOT` | `SST_DATA_ROOT` | `<root>/03_data` | — |
| `KNOT_DATASET` | `SST_KNOT_DATASET` | `03_data/A_knots/04_knotplot/final` | `KnotPlot/knots/final` |
| `IDEAL_SOURCES` | `SST_IDEAL_SOURCES` | `03_data/A_knots/01_ideal/ideal_sources` | `Ideal_Sources` |
| `KATLAS_SOURCES` | `SST_KATLAS_SOURCES` | `03_data/A_knots/03_katlas/v0.2.2` | `Katlas_Sources_v0.2.2_Outputs` |
| `FSERIES_ROOT` | `SST_FSERIES_ROOT` | `03_data/A_knots/02_fourier/knotplot_legacy` | `KnotPlot/Knots_FourierSeries` |

Root marker: [`.sst-workbench-root`](../../.sst-workbench-root) at the repo root.
If the marker is missing and `SST_WORKBENCH_ROOT` is unset, resolution raises
`WorkbenchRootNotFound` instead of walking to the filesystem root.

### `resolve_family(catalog_id, version=None)`

- Prefers `10_docs/registry/catalog_index.json` when present (SP08).
- Otherwise reads `10_docs/migration/path_map.csv`.
- Returns `new_path` if it exists on disk, else `old_path` (migration / junction era).
- When the same ID exists in multiple domains, prefers `01_research`, then
  `02_libraries`, then `05_apps`. Pass `domain=` to disambiguate.

## CMD — `07_scripts/paths.cmd`

```bat
call "%SST_WORKBENCH_ROOT%\07_scripts\paths.cmd"
rem or, from a pack:
call "%~dp0..\..\..\07_scripts\paths.cmd"

echo %SST_WORKBENCH_ROOT%
echo %SST_KNOT_DATASET%
```

Same override semantics: `if not defined X set "X=..."`. `:find_root` walks up
from `%~dp0` looking for `.sst-workbench-root`.

## Replacement patterns

```text
..\..\KnotPlot\knots\final        ->  %SST_KNOT_DATASET%  /  sst_workbench_paths.KNOT_DATASET
Path(__file__).parents[2]         ->  sst_workbench_paths.WORKBENCH_ROOT
'../../Ideal_Sources'             ->  sst_workbench_paths.IDEAL_SOURCES
C:\workspace\...\KnotPlot\knots   ->  %SST_KNOT_DATASET%
```

Bulk conversion of ~2,064 hardcoded paths is **out of scope** for SP01. Convert
opportunistically when a pack is touched; junctions keep old paths alive until SP11.

## First conversion targets (absolute `SST_WORKBENCH_ROOT`)

Listed only — **not converted in SP01**:

1. `SST_Maxwell/1_Maxwell_SST_Kinetic_Falsifier_v0.2.0/config/paths.cmd`
2. `SST_Maxwell/1_Maxwell_SST_Kinetic_Falsifier_v0.3.0/config/paths.cmd`
3. `SST_Maxwell/1_Maxwell_SST_Kinetic_Falsifier_v0.3.1/config/paths.cmd`
4. `SST_Einstein/Einstein_SST_Blind_Falsifier_v0.1.0/config/paths.cmd`

(Inventory at SP01 freeze: four `config/paths.cmd` files hardcode
`C:\workspace\projects\SST-Workbench`. Replace each with
`call …\07_scripts\paths.cmd` once SP02 junctions are ready.)

## Numeric domain prefixes are not Python packages

`import 01_research...` is a syntax error permanently. Catalog domains use leading
digits (`01_research`, `02_libraries`, …) so they must never be imported as
top-level modules.

SP00 Q2 scanned 301 `sys.path` call sites: **no research pack imports a sibling
top-level directory by name**. Most inserts reach the installed `sstcore`
package or pack-local code. Cross-pack access must use `resolve_family()` (or
`SST_*` env vars from `paths.cmd`), not `sys.path` + directory-name imports.

The only related conversion targets are tooling that import the root module
`sst_gilbert_usability` (breaks when that file moves into `07_scripts/` in SP04)
— that is a path-move issue, not a numeric-prefix issue. See
`10_docs/migration/open_questions.md` Q2.

## Tests

```text
python -m pytest scripts/test_workbench_paths.py scripts/test_resolve_family.py scripts/test_paths_cmd.py -q
```
