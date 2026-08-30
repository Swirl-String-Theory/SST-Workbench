# Knot_Library

Central SST-Workbench knot repository organized by **provenance**, not file format.

```text
Knot_Library/
├── SST_Knot_Library/SST_Knot_Library_v0.2.0/   # sst_knotlib package (v0.2.1+)
├── Sources/
│   ├── Ideal_Gilbert/                 # provider_id: gilbert_ideal
│   ├── FourierSeries_Fremlin/         # provider_id: fremlin_fourier
│   ├── KnotPlot_Scharein/             # provider_id: knotplot
│   ├── Ridgerunner_Cantarella_Rawdon/ # provider_id: ridgerunner
│   ├── KAtlas_BarNatan/               # provider_id: katlas
│   └── SST_Generated/                 # provider_id: sst_generated
├── Registry/
├── Derived/
└── Quarantine/
```

## Rules

- **Copy, do not move** upstream archives from `Ideal_Sources/`, `Ideal_Fremlin_Fseries/`, `KnotPlot/`, etc.
- Machine IDs live in `Registry/providers.json` and each provider's `SOURCE.json`. Software must not parse directory names for identity.
- Gilbert and Fremlin are **both** Fourier representations; they differ by construction objective (SONO/ideal vs elegant 3D realization).
- `KnotPlot_Scharein/SST_Relaxation_Campaigns/` holds RR-polished finals — **not** KnotPlot `Database_Original`.
- `KAtlas_BarNatan/` = topology/reference source data. `SST_Generated/KAtlasBraidDerived/` = SST 3D realizations of those braids.
- Unknown provenance → `Quarantine/`, never a strict falsifier input.
- Licence / redistribution status for upstream datasets remains **UNRESOLVED** (same policy as `Ideal_Sources/PROVENANCE.md`). Ship manifests and reconstruction scripts for referees.

## Setup helper

`_setup_provenance.py` scaffolds directories and copies known archives (idempotent). Re-run after adding new upstream batches.

## Inventory

```bat
cd SST_Knot_Library\SST_Knot_Library_v0.2.0
run_inventory.cmd
```

Writes regenerable `Registry/inventory_unmigrated.json` (gitignored) without moving files.
A compact `Registry/inventory_summary.json` is kept for quick counts.
