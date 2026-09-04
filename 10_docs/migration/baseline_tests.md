# SP00 baseline tests

Recorded during freeze before any research-pack moves.
Working tree accepted dirty for concurrent unpacks outside Phase A
(see `FREEZE.md` quiescence).

Freeze HEAD: `81650569` (PyYAML + workbench_tree ASCII help).

## Commands

```powershell
python -m pytest scripts/ -q
python -m unittest test_sst_gilbert_usability
python -m pytest verification-suites/embedded-knots/ -q
```

## As-found (before Phase A dependency fix)

| Suite | Result |
|-------|--------|
| `pytest scripts/` | **58 passed, 9 failed** |
| `unittest test_sst_gilbert_usability` | **4 passed** |
| `pytest verification-suites/embedded-knots/` | **1 skipped** |

All nine `scripts/` failures were:

```text
RuntimeError: PyYAML is required: pip install pyyaml
```

from `scripts/falsifier_registry.py`. PyYAML was used but missing from
`requirements-workbench.txt`.

## Post-fix (after `PyYAML>=6.0` install + requirements update)

| Suite | Result |
|-------|--------|
| `pytest scripts/` | **67 passed** (100.45s) |
| `unittest test_sst_gilbert_usability` | **4 passed** |
| `pytest verification-suites/embedded-knots/` | **1 skipped** |

### Final freeze run (after SP00 generators + tests)

| Suite | Result |
|-------|--------|
| `pytest scripts/` | **80 passed** (39.30s) |
| `unittest test_sst_gilbert_usability` | **4 passed** |
| `pytest verification-suites/embedded-knots/` | **1 skipped** |

Raw captures: `_pytest_scripts_post.txt`, `_pytest_scripts_final.txt`,
`_unittest_gilbert_post.txt`, `_pytest_embedded_post.txt`.

Later phases compare against the **final freeze** row (80 passed), not against
green-from-scratch. A regression is any new failure relative to this table.
