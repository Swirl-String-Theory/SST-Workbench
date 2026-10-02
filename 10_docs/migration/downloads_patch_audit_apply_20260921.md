# Downloads patch audit apply — 2026-09-21

Scope: fourteen zips from `Downloads/` checked against the catalog; residual gaps applied.

## Per-zip verdict

| Zip | Catalog target | Verdict |
|-----|----------------|---------|
| `E010_pklsa_parametric_knot_link_seed_atlas_v0.3.0.zip` | E010-v0.3.0 | Already applied (74/74 match) |
| `SST_Parametric_Trefoil_Seed_Atlas_v1.0.0.zip` | E009-v1.0.0 | Already applied (56/56 after CRLF normalize) |
| `SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.1.zip` | A038-v0.3.1 | Already applied (74/74) |
| `Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1.zip` | A041-v0.3.1 | Already applied (156/156) |
| `Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0.zip` | A041-v0.3.0 | Applied; **vendor zip restored** 2026-09-21 |
| `SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.0.zip` | A042-v0.1.0 | Already applied |
| `QGI_v0.1.0_MSVC_ssize_t_fix_patch.zip` | A042-v0.1.0 | Already applied (`cpp` + `run_02` match) |
| `QGI_v0.1.0_setup_discovery_fix_patch.zip` | A042-v0.1.0 | Already applied (`setup.py` match; `run_02` kept MSVC variant) |
| `..._v0.1.1_BLIND_SOURCE.zip` / `..._REVEAL_KEY.zip` | A042 `_variants/` | Already applied (CRLF); local `run_02` left untouched |
| `SST_Paper_Driven_Falsifier_Upgrade_Patches_2026-09-07.zip` | many | P0/P1 + deferred already present; **A016/A024/A025 optional controls added** to version dirs |
| Cosmic Gamma BLIND + both outputs zips | **A044-v0.1.0** (new) | **Imported** 2026-09-21 |

## Applied this session

1. **A044** Cosmic Gamma Transparency Dispersion Lorentz Emergence
   - Path: `01_research/A_falsifiers/A044_cosmic_gamma_transparency_dispersion_lorentz_emergence/`
   - Source → `A044-v0.1.0/` (`.pytest_cache` excluded)
   - Outputs unpacked under `A044-v0.1.0/outputs/{blind,revealed}/`
   - Output zips beside family; registry + `falsifier_registry.yaml` updated; `next_catalog_ids.A_falsifiers=A045`
2. **Optional paper-control** files into `A016-v0.1.1`, `A024-v0.3.0`, `A025-v0.3.0` (`PAPER_UPGRADE.md`, `paper_upgrade/`, `run_paper_upgrade.cmd`). Note: `git apply` inside those trees skipped patches (already mirrored under `_variants/optional-paper-control`); files were taken from a clean empty-tree apply of the same diffs. No `latest` bumps.
3. **A041-v0.3.0** `vendor/SST_Knot_Library_v0.2.5.zip` restored; SHA-256 matches sidecar.
4. **Archive:** ten missing zips copied into `09_archive/restore/{Trefoil,Falsifiers}/` (four already identical).

## Tests

| Suite | Result |
|-------|--------|
| `07_scripts/test_catalog_registry.py` + hierarchy + resolve | **23 passed** |
| A044 `pytest tests` | Collection error: native `_native` extension not built (expected for structural import; run `setup.py` / pack build before scientific runs) |

## Explicit non-actions

- No re-extract of E009/E010/A038/A041-v0.3.1/A042 packs
- No re-apply of paper-upgrade diffs whose target versions already had `paper_upgrade/`
- No overwrite of A042 variant `run_02_build_native.cmd`
