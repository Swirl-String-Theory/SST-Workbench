# SST-Workbench — To_Be_Proccessed


Purpose
-------
This folder is a quarantine/integration inbox. Do NOT move these candidates directly into the canonical namespaces without validating provenance, catalog IDs, manifests and duplicate content first.


Current canonical root:
C:\workspace\projects\SST-Workbench


Items staged here
-----------------

1. E010_candidate_SST_Parametric_Knot_Link_Seed_Atlas_v0.1.1
   Status (2026-09-21): INTEGRATED as E010 family (latest E010-v0.3.0 from Downloads zip;
   v0.1.1 metadata under E010-v0.1.1). **98 npz still MISSING** — see
   `10_docs/migration/to_be_processed_e010_pc_20260921.md` and
   `E010-v0.1.1/GEOMETRY_RESTORE.md`. Keep staged copy until authentic geometry restore.


2. Production_Certification_and_Paper_Upgrade_2026-09-08
   Status (2026-09-21): PROCESSED — unique reports copied to `10_docs/migration/`;
   PC01–PC04 remapped targets implemented (D006-v0.4.1, A037-v0.3.3, A034-v0.2.3,
   A038-v0.5.1, C006-v0.2.2 cert-only). Plans remain canonical under
   `.cursor/plans/paper_upgrade/`.

3. Falsifier template repair
   The canonical source folder already exists at:
   06_templates/SST_Blind_MultiLibrary_Falsifier_Template_v0.1.0
   The sibling ZIP previously observed in Drive is only 22 bytes and should be treated as invalid.
   Rebuild the ZIP FROM THE EXISTING SOURCE FOLDER, verify it opens, then generate SHA-256.
   Do not replace the source folder.


Library-only artefacts NOT byte-copied by the Drive connector
--------------------------------------------------------------
These exist in ChatGPT Library/history but were not found as Drive-native source files. Import/recover them separately before declaring the Workbench complete:


Evidence Canon:
- SST_Evidence_Canon_v0.1.0.tex
- SST_Evidence_Canon_v0.1.0.pdf
- SST_Evidence_Canon_v0.2.0.tex
- SST_Evidence_Canon_v0.2.0.pdf
- related claim/evidence ledger if present in the originating package


Euler/BKM:
- SST_Euler_Regularity_BKM_Singularity_Gate_v0.1.0_to_v0.2.0.diff
- VALIDATION(20260911-003556).md
- recover/rebuild the actual v0.1.0 and v0.2.0 package directories/ZIPs from the originating chat artefacts if available


Trefoil / A038 provenance:
- SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.2.zip.sha256
- SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.3.2_to_v0.3.3.diff
- recover the actual v0.3.2 package/ZIP before registering it


KnotLinkAtlas:
- KnotLinkAtlas_v032_local_run_2026-09-04.zip.sha256
- recover the matching ZIP before marking the run bundle present


Geometric Master-Mass campaign:
- SST_Geometric_Master_Mass_Closure_Blind_Falsifier_v0.1.0-preregistration.zip.sha256
- SST_Geometric_Master_Mass_Closure_Blind_Falsifier_v0.1.0-source-audit-addendum.zip.sha256
- recover the matching ZIPs before integrating


Catalog-ID warning
------------------
The registry snapshot from 2026-09-13 still advertises A043 and E010 as the next IDs, but a physical A043 Knot State Algebra family already exists in Drive. Therefore:
1. Do NOT assign Euler/BKM to A043.
2. Scan the physical tree first.
3. Regenerate 10_docs/registry/catalog_index.json.
4. Regenerate 10_docs/registry/family_hierarchy.json.
5. Regenerate/update falsifier_registry.yaml.
6. Only then allocate the next free A_falsifiers ID (likely A044 if no other physical collision exists).
7. Only then allocate/integrate the PKLSA pipeline under the next free E_pipelines ID.


Canonical naming rules
----------------------
Family directory: {catalog_id}_{slug}
Version directory: {catalog_id}-{version_id}
Prefer version form vMAJOR.MINOR.PATCH.
Each family root should have FAMILY.yaml.
Each version directory should have project.json.
Keep historical output names stable.
Blind/reveal material must remain separated.
Do not merge private reveal keys into blind packages.


Suggested IDE workflow
----------------------
1. Inventory this To_Be_Proccessed folder recursively.
2. Compare every candidate against the canonical tree by SHA-256 and relative content.
3. Classify each file as:
   - exact duplicate -> discard staged copy;
   - newer/unique -> integrate;
   - provenance-only -> place under 10_docs/migration or the owning family;
   - unresolved -> leave in To_Be_Proccessed and document why.
4. Repair the 22-byte template ZIP from its canonical source folder.
5. Recover Library-only artefacts listed above.
6. Resolve the A043 collision.
7. Integrate PKLSA only after registry regeneration.
8. Rebuild catalog_index.json and family_hierarchy.json from the physical tree.
9. Run reproducibility/validation gates for affected active families.
10. Generate a final migration report with old path, new path, SHA-256, action and rationale.
11. Delete To_Be_Proccessed only when all items have been accounted for.


Do not silently overwrite canonical scientific results. Prefer copy + compare + verified move.