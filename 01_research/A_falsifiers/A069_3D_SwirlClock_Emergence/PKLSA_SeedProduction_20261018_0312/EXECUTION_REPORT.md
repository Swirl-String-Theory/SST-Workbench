# PKLSA KnotPlot Seed Production v0.1.0 — lokaal uitvoeringsverslag

Uitgevoerd op 18 oktober 2026 op de thuis-pc, binnen SST-Workbench. Alle geometrieën zijn uitsluitend dimensieloze statische seeds; geen fysisch gevalideerde vortexoplossingen.

Python 3.14.3, NumPy 2.4.6; KnotPlot 1.022 build 5125W. ZIP SHA256: `acedabd028dbedaa23b6ef2b3e29f85a8c763e3c28efb1e049ffef97a75c48af`.

## Gates

- **PASS — PACKAGE_INTEGRITY**: 59/59 bundled SHA256 entries match; original ZIP retained.

- **PASS — REGRESSION**: 5 unittest tests passed, exit 0.

- **PASS — S0_GENERATED_PROVENANCE**: Two frozen formulas, 16 manifest rows with source/mirror/provider lineage and SHA256. One shared notebook provider group, not 16 providers.

- **UNRESOLVED — S0_ORIGINAL_NOTEBOOK_AUTHENTICITY**: Original notebook page images/bytes are not included; historical formula transcription authenticity not independently verified.

- **PASS — S1_STATIC_GEOMETRY**: 16/16 STATIC_QA_PASS: finite closed single components, edge QA; dimensionless.

- **PASS — S2_MIRROR_PROJECTION**: 16/16 three-crossing signed projection regressions, including after actual ASCII reload; not an isotopy proof.

- **PASS — S3_RESOLUTION_LADDER**: N=128,256,512,1024 generated for A/B and exact z mirrors. This is geometric consistency, not solver convergence.

- **PASS — S4_INSTALLED_KNOTPLOT**: 16/16 LOCD loads and ASCII reloads; coordinate comparator exit 0 at rtol=atol=1e-12; one component and matching bead counts. No command-error diagnostics in checked import logs.

- **FAIL — RAW_COORDS_COMPARATOR**: Packaged comparator rejects KnotPlot coords output header Component 0:. coords is six-decimal output; save ... ascii supplies high precision. Supplied KPC overwrites its coords file with ASCII save; separate local wrappers preserve both formats. Original failure log retained.

- **FAIL — LEGACY_AUDITOR_AS_SHIPPED**: All 49 files initially UNPARSEABLE because raw.decode uses unknown encoding utf8-sig. Exit 0 does not imply valid inventory. Original results retained.

- **PASS — LEGACY_AUDIT_CODEC_FIXED**: Separate companion copy changes encoding spelling only to utf-8-sig; 49 raw files inventoried; 0 unparseable. No historical file changed or promoted.

- **FAIL — PKLSA_EXISTING_INSTALLATION**: E010 v0.3.1 source facade executes doctor via explicit PYTHONPATH; main venv has no installed sst_pklsa. Doctor exit 0 but coverage.pass=false: 10/11 required sources resolved; pipeline.ptsa_e009 missing. No repair/import attempted.

- **UNRESOLVED — S5_RUNTIME_AND_RELAXATION**: Actual reset parameter dump collected: close=0.12, max-dr=0.10; executable SHA recorded. Preparation scripts generated only; no prep, fitto, go-1 or dynamics executed. Full safety/calibration and independent seeds remain unqualified.

- **UNRESOLVED — S6_INDEPENDENT_TOPOLOGY**: No independent Alexander/link-isotopy certificate executed; projection regression alone is insufficient.

- **UNRESOLVED — S7_FINITE_CORE**: No finite-core tube, nonlocal clearance/reach or core-to-mesh qualification.

- **UNRESOLVED — S8_PHYSICAL_DYNAMICS**: No Euler/pressure-Poisson, space/time/core/backend convergence or phase qualification; static seeds only.

- **PASS — E010_PRESERVATION**: 40466 existing E010 v0.3.1 files hashed before/after with no differences (excludes venv/build/cache).

- **UNRESOLVED — GLOBAL_RESEARCH_SNAPSHOT**: Metadata snapshot covered 269102 files in 01_research and 03_data. 67 changes all under concurrent A068 execution_20261018_home; no writes by this run targeted that tree. No repo-wide byte hash claim.

## Uitvoer en reproduceerbaarheid

- `PKLSA_KnotPlot_SeedProduction_v0.1.0/production_out/`: 16 XYZ, 16 LOCD, manifest, candidate metadata, import/checkpoint exports and generated preparation scripts.
- `commands.json`, `logs/`, `extra_validation.json`: commands, exit codes, runtime logs and import evidence.
- `runtime_calibration.json`, `runtime_parameters.txt`, `environment.json`: actual executable/parameter provenance.
- `legacy_quarantine_inventory.csv`: original failed audit; `legacy_quarantine_inventory_codec_fixed.csv`: separate corrected audit.
- `preservation.json`, `E010_hashes_before.json`, `protected_metadata_before.json`: preservation evidence.

Generated sample versus bundled example: largest absolute coordinate difference 6.4503957730721595e-14. Byte identity across platform/NumPy builds is not asserted; original sample and new files retained.

## Begrenzing

Geen E010-import, registrywijziging, frozen-falsifier run, relaxatiecampagne, commit of push uitgevoerd. Het originele pakket blijft ongewijzigd; companion scripts en alle nieuwe outputs staan uitsluitend in deze deliverables-map. S5–S8 en authenticatie van de oorspronkelijke notebookpagina’s vereisen afzonderlijk werk. De bestaande PTSA-bronresolutie moet worden hersteld voordat PKLSA-brede volledigheid kan worden geclaimd.
