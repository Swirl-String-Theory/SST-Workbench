# Falsifier registry

Single source of truth for SST falsifier packs: [`../falsifier_registry.yaml`](../falsifier_registry.yaml).

Rendered inventory: [`../INVENTORY_FALSIFIERS.md`](../INVENTORY_FALSIFIERS.md).

## Schema

Each entry has a stable `SST-FALS-{family}-{nn}` ID and belongs to one of five scientific families:

| Family | Theme |
|:---:|:---|
| I | Dynamic particle stability |
| II | Local mode / field structure |
| III | Gravity / pressure / emergent fields |
| IV | Energy / thermodynamics / Maxwell–Kelvin |
| V | Anti-self-deception / metrology |

## Physics vs numerics

Update **both** fields after a campaign:

| Field | Meaning |
|:---|:---|
| `physics_status` | Blind gate / hypothesis outcome: `PASS`, `FAIL`, `INDETERMINATE`, `UNTESTED`, `REFERENCE_ONLY` |
| `numerics_status` | Build, pytest, native parity: `PASS`, `FAIL`, `NOT_RUN`, `N/A` |

**Rule:** `numerics_status: PASS` must never be read as `physics_status: PASS`.

## After a blind campaign

1. Seal results and note `result_sha256` (from pack `MANIFEST.sha256` when available).
2. Edit `falsifier_registry.yaml`: set `physics_status`, optional `result_sha256`, and `next_test`.
3. Regenerate the markdown inventory:

```bash
python scripts/render_falsifier_inventory.py --write
```

4. Validate:

```bash
python scripts/falsifier_registry.py --validate
python -m unittest scripts.test_falsifier_registry
```

## CI / drift checks

List working-tree packs not covered by any registry glob:

```bash
python scripts/falsifier_registry.py --discover
```

Pack paths and versions are auto-resolved from working trees + `Restore_Archives/` zips (latest semver per `pack_glob`).
