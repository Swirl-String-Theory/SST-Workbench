# SST-Workbench

Exploratory proof scripts, verification suites, GUI dashboards, notebooks,
generated figures, datasets, and experimental workflows supporting
[SSTcore](https://github.com/Swirl-String-Theory/SSTcore) and
[Swirl-String-Theory](https://github.com/Swirl-String-Theory/SwirlStringTheory).

This repository is **not** the canonical source for SST definitions.

| Repository | Role |
|------------|------|
| [SwirlStringTheory](https://github.com/Swirl-String-Theory/SwirlStringTheory) | Canonical theory — `papers/SST-CANON/` |
| [SSTcore](https://github.com/Swirl-String-Theory/SSTcore) | Stable Python/C++ API — `pip install SSTcore`, `examples/` |
| **SST-Workbench** (this repo) | Research sandboxes, dashboards, migration archive |

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install SSTcore
python -m pip install -r requirements-workbench.txt
```

Run commands from the repository root.

## Common entry points

| What | Path | Command |
|------|------|---------|
| SSTcore dashboard | `gui/dashboard/sstcore/sst_dashboard_app.py` | `python gui/dashboard/sstcore/sst_dashboard_app.py` |
| Swirl dashboard | `gui/dashboard/swirl/sst_dashboard_app.py` | `python gui/dashboard/swirl/sst_dashboard_app.py` |
| Full probe harness | `proof-scripts/SSTcore_full_probe.py` | `python proof-scripts/SSTcore_full_probe.py` |
| Embedded-knots tests | `verification-suites/embedded-knots/` | `pytest verification-suites/embedded-knots/` |
| Derive constants (BEM, trefoil) | `experiments/derive_constants/` | See scripts per subfolder — [layout doc](WORKBENCH_LAYOUT.md) |
| Chi-phase packages | `to_be_processed/sst_chi_phase_package_v*/` | Each package has its own `README.md` |

## Layout

| Path | Contents |
|------|----------|
| `experiments/derive_constants/` | Finite-cell derivation program (from canon `Derive_Constants/`) |
| `experiments/derive_constants/bem/` | BEM / CoilLab / routeB outputs (sorted) |
| `experiments/trefoil/closure/` | Trefoil closure packages from dashboards |
| `gui/dashboard/` | PyQt dashboards (`sstcore/`, `swirl/`) |
| `proof-scripts/` | Python proof harnesses and examples |
| `datasets/` | SPARC, exports, swirl resources |
| `generated-figures/` | Resource results and proof plots |
| `media/` | Images, presentations, voiceovers |
| `archive/` | Swirl archive + merge conflict losers |
| `to_be_processed/` | Chi-phase research packages (v10–v16) |
| `verification-suites/` | Standalone verification scripts |

See also:

- [WORKBENCH_LAYOUT.md](WORKBENCH_LAYOUT.md) — full directory map and source origins
- [MIGRATION_MANIFEST.md](MIGRATION_MANIFEST.md) — move-only migration log (rev. 5)
- [CONFLICT_RESOLUTION.md](CONFLICT_RESOLUTION.md) — Derive_Constants merge rules
- [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md) — post-migration integrity checks

## Not in git

Large or generated binaries are kept locally and excluded via `.gitignore`:

| Excluded | Reason |
|----------|--------|
| `bundles/`, `*.zip` | Large zip bundles (e.g. trefoil closure) |
| `hardware/` | 3D-print assets (STL, gcode, OBJ) |
| `*.pyd` | Compiled SSTcore extensions — install via `pip install SSTcore` |
| `*.blend`, `*.blend1` | Blender scene files |
| `.idea/`, `.venv/` | IDE settings and local virtualenv |

These assets originated from SwirlStringTheory and SSTcore during the rev. 5 migration. See [MIGRATION_MANIFEST.md](MIGRATION_MANIFEST.md) for source paths.

## Line endings

Text files use **CRLF** on Windows, enforced by [`.gitattributes`](.gitattributes).

## Migration notes

- Move-only migration (rev. 5): no files deleted; losers archived under `archive/conflict-losers/`.
- Frozen in SwirlStringTheory: `papers/VAM/`, rest of `papers/`, `tools/`, `out/`.
- Derive_Constants merge log: [CONFLICT_RESOLUTION.md](CONFLICT_RESOLUTION.md).
