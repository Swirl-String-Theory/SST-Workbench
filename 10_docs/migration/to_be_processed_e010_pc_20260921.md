# To_Be_Processed intake — E010 PKLSA + Production Certification — 2026-09-21

## Summary

| Inbox item | Action | Result |
|------------|--------|--------|
| `E010_candidate_SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1` | Integrate + restore attempt | Family at `01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/`; **98 npz unresolved** |
| `Production_Certification_and_Paper_Upgrade_2026-09-08` | Docs merge + PC01–PC04 | Reports under `10_docs/migration/`; remapped targets landed |

Registry regen: `next_catalog_ids.A_falsifiers=A044`, `E_pipelines=E011` (A043 + E010 physical collisions resolved).

## E010

### Geometry restore (unresolved)

| Check | Result |
|-------|--------|
| `rclone gdrive:SST-Workbench` | Path missing on Drive root |
| Local / Downloads `SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1` zip with npz | Not found |
| A041-v0.4.1 vendored dataset | Metadata only; no `families/` / `base_geometries/` |
| PTSA zip hash | Matches `SOURCE_HASHES` (`11b7eb4e…`) |
| `Ideal_Sources_Official.zip` | Not found |

See [GEOMETRY_RESTORE.md](../../01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.1.1/GEOMETRY_RESTORE.md).

### Integrated paths

| Old / source | New | Action |
|--------------|-----|--------|
| Downloads `E010_pklsa_*_v0.3.0.zip` | `01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/` (FAMILY + E010-v0.3.0) | extract / integrate (canonical latest) |
| `To_Be_Proccessed/E010_candidate_…_v0.1.1` | `…/E010-v0.1.1/` | copy metadata; geometry_status=MISSING_NPZ |
| A041 `datasets/SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1` | unchanged | vendored consumer only |

## Production Certification

### Docs

| Source | Destination | Action |
|--------|-------------|--------|
| `TOTAL_REPORT_2026-09-08.md` | `10_docs/migration/paper_upgrade_TOTAL_REPORT_2026-09-08.md` | unique migration copy |
| `PC00_REPORT_2026-09-08.md` | `10_docs/migration/paper_upgrade_PC00_REPORT_2026-09-08.md` | unique migration copy |
| `*.zip` reports/plans | `10_docs/migration/` | provenance archive |
| Plan bodies | `.cursor/plans/paper_upgrade/` | already present; not duplicated |

Parent plan remapped: [PRODUCTION_CERTIFICATION.plan.md](../../.cursor/plans/paper_upgrade/PRODUCTION_CERTIFICATION.plan.md).

### Version bumps landed

| Patch | Target | Key artifact |
|-------|--------|--------------|
| PC01 | D006-v0.4.1 | `pc01_regressions.py` Tests A/B/C |
| PC02 | A037-v0.3.3 | `pc02_qualification.py` |
| PC03 | A034-v0.2.3 | `pc03_dual_branch.py` |
| PC04 | A038-v0.5.1 | `pc04_firewall.py` + `/preflight` |
| P1 | C006-v0.2.2 | `pc_cert_provenance.py` (P26 stays in v0.2.1) |

PC05 deferred.

## Tests run (2026-09-21)

- `07_scripts/test_paper_upgrade_gates.py` (+ certificate/numerics): pass
- D006/A037/A034/A038/C006 PC unit tests: pass
- E010-v0.1.1 packaging tests: pass

## Quarantine status

Leave `To_Be_Proccessed/` in place until npz restore succeeds or E010-v0.1.1 is explicitly retired. Do not delete inbox yet.

## Out of scope (unchanged)

Evidence Canon, Euler/BKM, falsifier template ZIP, PU05–PU08 campaigns, A029/A030 bumps.
