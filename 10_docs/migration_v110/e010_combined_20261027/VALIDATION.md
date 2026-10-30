# E010 v0.4.0 combined atlas - final validation

Status: **PASS_COMBINED_ATLAS_ACCEPTANCE**. Source intake and portable geometry packaging only; no scientific campaign or status promotion.

- 11,757 logical records: 4,497 historical, 3,630 nominal Ruban and 3,630 perturbed Ruban.
- 10,169 original Ruban manifest entries pass; 10,164 component files contain 1,024 finite XYZ points each.
- 40,359 historical output files and 2,282 original source paths retain their hashes. Every original carrier qualification record is preserved exactly.
- 17 targeted regression tests pass. All historical parsed geometry hashes were checked during the build.
- The portable ZIP passed CRC, full payload hash checks and isolated loading of 14 representative geometry cases from its own extracted data.
- The unchanged rerun passed PASS_IDEMPOTENT_VERIFICATION; all previous artifacts and logs remain.
- The three-page intake PDF was rendered and every page inspected; PDF_VISUAL_QA.json records the checks and non-fatal Poppler font-map warnings.
- E010 v0.4.0 is registered using the existing builders. Other catalog family nodes are unchanged. Existing latest=v0.3.0 and scientific gate are preserved.
- 1,452 nominal topology IDs (and their perturbed children) remain unmapped. 54,450 proposed scenarios remain PENDING/NOT_RUN. Research inclusion is explicit opt-in.
- The parsed index contains 11,075 distinct ordered geometry hashes, with 303 duplicate groups. Every logical record is retained.

## Artifacts

Version: `01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.4.0/`.

Output: `E010-v0.4.0/SST_Parametric_Knot_Link_Seed_Atlas_v0.4.0_outputs/`.

ZIP, SHA-256 sidecar and technical PDF are published in the E010 family parent directory.

## Execution

From E010-v0.4.0: `run_all.cmd` (build once or verify unchanged publication), `run_all.cmd SELFTEST`, or `run_all.cmd VERIFY`.

From an extracted ZIP: `py -3.14 -B verify_atlas.py`. The NumPy reader uses only relative geometry paths inside that payload. `allow_research=True` explicitly selects research geometry and does not qualify it scientifically.

## Next scientific use

The atlas is available for explicit data selection. A011/A054/A065 and their pinned dataset contracts were not edited. A future falsifier release needs its own dataset-admission contract and bounded execution authorization. Scheduled settings were not changed.

## Hashes

Intake source contract: `108233548e33db19e93a149c752e1d16532a5e6f8b9aee2e01533689ac49107e`

Combined index: `70af49e67406e26187607eef5c624a88989e8fd5938d0c6f42ba3b2d23b75341`

Portable ZIP: `2051ad2e9a0b51857197e6688b09d9be48bd562c01ec0e7613eddfebeb174d82`

