# SST cpp_pybind audit template

Minimal starter for SST Workbench audits with:

- `cpp/` — pybind11 kernel (rebuild on source change)
- `native_ext/` — Python package (loader, fallback, core logic)
- `run_*.py` — CLI entry points
- `run_install.cmd` / `run_all.cmd` — one-command Windows install + full battery

Copy this entire folder, rename `native_ext/` and edit `native_ext/_config.py` before adding your real kernel.

## Layout

```
SST_cpp_pybind_audit_template/
├── README.md
├── run_install.cmd         # .venv + pip install -r requirements.txt
├── run_all.cmd             # install -> build -> run_all_checks.py
├── run_example.py          # single run (all flags)
├── run_sweep.py              # parameter sweep
├── run_all_checks.py         # smoke + sweep battery
├── cpp/
│   └── native.cpp            # pybind11 module (_native)
├── native_ext/
│   ├── _config.py            # names/paths — edit first after copy
│   ├── build_ext_if_needed.py
│   ├── core.py
│   └── fallback.py
├── examples/
│   ├── minimal_commands.txt  # quick copy-paste commands
│   └── full_commands.txt     # every CLI flag illustrated
├── tests/
└── build/                    # generated (stamp + setup helper)
```

Outputs land inside the package as `{folder_name}_outputs/` (e.g. after rename to `Foo_v0.1.0` → `Foo_v0.1.0/Foo_v0.1.0_outputs/`).

## Quick start (Windows)

```bat
cd SST_cpp_pybind_audit_template
run_all.cmd
```

That creates `.venv`, installs requirements, attempts a C++ build, and runs the full check battery into `{folder}_outputs/`.

Manual / cross-platform:

```bash
cd SST_cpp_pybind_audit_template

# 1. Build C++ (optional; Python fallback works without it)
python -m native_ext.build_ext_if_needed --force

# 2. Smoke test
python run_example.py

# 3. Full battery -> {folder}_outputs/
python run_all_checks.py
```

After copying, change at minimum:

| File | What to edit |
|------|----------------|
| `native_ext/_config.py` | `PACKAGE_NAME`, `EXT_BASENAME`, `CPP_REL`, `LOG_PREFIX` |
| `cpp/native.cpp` | Your pybind11 exports |
| `native_ext/core.py` | `run()`, `run_audit()`, `run_sweep()` |
| `native_ext/fallback.py` | Pure-Python equivalent |
| `run_example.py` | Import path if you renamed the package folder |

## C++ rebuild behaviour

`build_ext_if_needed.py` hashes `cpp/*.cpp` and writes `build/*.stamp.json`. The extension rebuilds only when sources change, unless you pass `--force`.

Load order in `core.run()`:

1. Auto-build if needed (unless `--skip-build`)
2. Import `_native*.pyd` / `.so`
3. Fall back to `fallback.py` on failure or with `--force-python`

## CLI reference

### `python -m native_ext.build_ext_if_needed`

| Flag | Description |
|------|-------------|
| `--force` | Rebuild even when stamp hash matches |
| `--quiet` | Suppress compiler log |
| `--strict` | Exit 1 if extension missing after build |

### `python run_example.py`

| Flag | Default | Description |
|------|---------|-------------|
| `--a` | `2.0` | First operand |
| `--b` | `3.0` | Second operand |
| `--expected` | `a+b` | Pass/fail reference value |
| `--force-python` | off | Skip C++, use fallback |
| `--skip-build` | off | Do not auto-build before run |
| `--force-build` | off | Force rebuild before run |
| `--build-verbose` | off | Print compiler commands |
| `--out` | — | Write JSON result (bare names → `{folder}_outputs/`) |
| `--summary-only` | off | One-line PASS/FAIL |

### `python run_sweep.py`

| Flag | Default | Description |
|------|---------|-------------|
| `--values-a` | `1.0,2.0,3.0` | Comma-separated `a` list |
| `--values-b` | `0.5,1.5,2.5` | Comma-separated `b` list |
| `--force-python` | off | Python fallback only |
| `--skip-build` | off | Skip auto-build |
| `--force-build` | off | Force rebuild |
| `--build-verbose` | off | Verbose build log |
| `--out-json` | `{folder}_outputs/sweep.json` | Sweep JSON |
| `--out-csv` | `{folder}_outputs/sweep.csv` | Sweep CSV |

### `python run_all_checks.py`

| Flag | Default | Description |
|------|---------|-------------|
| `--out-dir` | `{folder}_outputs` | Output folder |
| `--force-python` | off | Run primary smoke in Python mode |
| `--force-build` | off | Force C++ rebuild first |

Writes: `smoke_cpp.json`, `smoke_python.json`, `sweep.json`, `sweep.csv`, `audit_summary.json`.

## Example commands

**Quick tests** — see [`examples/minimal_commands.txt`](examples/minimal_commands.txt):

```bash
run_all.cmd
python -m native_ext.build_ext_if_needed --force
python run_example.py
python run_example.py --a 2 --b 3 --out example_cpp.json
python run_example.py --a 2 --b 3 --force-python --out example_python.json
python run_sweep.py --values-a 1,2 --values-b 0.5,1.5
python run_all_checks.py
```

**Every flag** — see [`examples/full_commands.txt`](examples/full_commands.txt).

## Dependencies

- Python 3.10+
- `numpy` (optional for richer fallbacks; template fallback is pure Python)
- `pybind11` + C++17 compiler for the fast path (`pip install pybind11`)
- `pytest` for `tests/`

On Windows, if direct `g++` compile fails, the builder falls back to `setuptools build_ext --inplace`.

## Extending

1. Replace `add(a,b)` in C++ and fallback with your kernel.
2. Add parameters to `run_audit()` and mirror them in `run_example.py` argparse.
3. Add refinement/probe scripts (`run_*_refinement.py`) following the horn BEM package pattern in `to_be_processed/sst_horn_neumann_bem_package/`.
