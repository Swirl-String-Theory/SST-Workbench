# Framework v1.0.10 report and output contract restoration

Date: 2026-10-26. Scope: framework audit, shared report/output binding and bounded A011 validation. Scientific campaigns and automatic scheduling remain disabled.

## Finding and implementation

The scientific report structure was not removed from Framework v1.0.10. The v1.0.6 and v1.0.7 report modules are byte-identical, with SHA-256 `c1bde86ac5fa008c93e4a5420fc1959fd44ddaef911402022027f494452dca5c`. The qualified v1.0.10 module has SHA-256 `3ecec6257027cee1a34b5190f282fe9492f39d1680a7fd64993d98daedba354e` and retains all 16 required protocol markers. It adds qualification and execution identity handling. The generic framework run_all entry is also retained. The audit and exact module diff are in FRAMEWORK_AUDIT.json and framework_report_107_to_110.diff.

The A011 migration lacked the scientific TeX template and automatic science/results bindings. Its version-local run_all still invoked the older demonstrations instead of the controlled migration adapter. A technical migration PDF occupied the report role without the complete scientific explanation. The cause is missing adapter binding and incomplete migration configuration.

The restored implementation uses the existing qualified framework functions assert_report, write_auto_science_tex, write_auto_results_tex and publish_instance_report. Existing output reservation, manifests and deterministic ZIP functions are reused. The shared adapter in 07_scripts/sst_migration/report_output_contract.py supplies measured A011 tables and plots to that renderer; it does not replace the scientific report generator. No qualified framework distribution bytes were modified.

A011-v0.4.1 is a patch successor of the sealed v0.4.0. Both v0.3.1 and v0.4.0 were preserved byte-for-byte. The requested v0.4.0 entry point was audited; executable correction and repeat-run validation were performed on v0.4.1 to respect historical immutability. The scientific contract, admitted geometry plan, thresholds, native binary and physical input requirements are unchanged.

## Restored contract

The standalone version-local run_all.cmd changes to its own directory, runs 39 targeted tests and then executes the bounded geometry adapter and scientific publication. SELFTEST executes tests only. Unsupported campaign modes are rejected. Runtime requirements are CPython 3.14, the existing ABI-compatible Windows native module and numerical packages, matplotlib, pdflatex, and access to the pinned framework and admitted local PKLSA sources. No native rebuild or new package installation was performed.

The stable namespace is A011_Maxwell_SST_Kinetic_Falsifier. Current results reside in A011-v0.4.1/A011_Maxwell_SST_Kinetic_Falsifier_v0.4.1_outputs/. Earlier output trees are reserved under their original run IDs. Each publication places a unique run-ID scientific PDF, ZIP and SHA-256 sidecar in the family directory one level above the version. LATEST_RUN.json is an atomic pointer; PUBLICATIONS.jsonl retains publication history. Failed attempts remain available without being registered as successful publications.

The scientific PDF includes the 14 requested topic groups and all 16 framework protocol markers, plus references. Primary science-contract statements, code mappings, input limitations and frozen protocol are explicit. Automatic results derive from the actual gate ledger and measured geometry. Graphs show the measured N=64/N=128 length and writhe sensitivity; no continuum convergence or SI calibration is asserted. Technical migration reports remain separate. The common admission requirement for future migration publications is recorded in 10_docs/migration_v110/REPORT_OUTPUT_CONTRACT.json.

## Validation and diagnostics

The qualified framework's 112 manifest entries are rechecked against their unchanged source pin. A059-v0.2.0 and A060-v0.2.1 scientific PDFs and source TeX were inspected as functional references and their original hashes retained.

The first unpublished candidate failed PDF compilation because an optional fvextra verbatim customization conflicted with framework-generated TeX. Removing that customization restored the existing standard framework environment. Two intermediate successful publications were retained. A reference line-wrap defect found during PDF inspection was then corrected in the unpublished source draft, with earlier source drafts and protocols archived. These were presentation corrections, not scientific changes or historical manifest edits.

Final standalone attempts 4 and 5 exited 0, with 39 tests passing in each run, followed by the three admitted geometries at N=64 and N=128. Both final PDFs contain eight pages. The latest rendered pages were visually inspected. REPORT_PACKAGING_GATES_FINAL.json records:

- All 14 requested report topic groups and 16 framework protocol markers present.
- REPORT_DATA gate records exactly equal the machine-readable ledger, including qualifications and dependent-claim authority.
- Plot data exactly equal measured geometry results.
- Generated framework TeX reproduces byte-for-byte from the corresponding inputs.
- Science-evidence and output manifests verified; ZIP CRC and every manifest payload hash verified.
- Embedded and externally published scientific PDFs are byte-identical; SHA-256 sidecars match the ZIPs.
- Repeated runs preserve the first published PDF, ZIP and sidecar and retain prior output trees.
- Historical A011 versions, reference reports, science contract and thresholds remain unchanged.

The final registration verifier independently checks source inventories, source archive, framework pins, registry scope and paused scheduling. Only A011's new version is registered; other pilot queue records remain unchanged. Migration, execution and scientific axes are retained separately. The queue is updated atomically under its existing lock.

Final audit note: the immediate pre-registration queue capture contains 43843 NUL bytes and is not valid JSON. It is preserved as evidence rather than repaired or reconstructed. The live queue is valid JSON. The final verifier compares every other job and A011's scientific axes with the intact earlier queue.before_schedule_registration.json baseline. That comparison passes, but exact immediately preceding queue bytes cannot be established from the invalid capture. This limitation is recorded in FINAL_REGISTRATION_VALIDATION.json as PASS_WITH_AUDIT_NOTE; it does not invalidate the independently verified scientific PDFs or output/source archives.

## Final publication and hashes

Latest run ID: `20261026T184203243717Z-0d021239`.

- Scientific PDF SHA-256: `a18b35cd1a3d0c7d6aeb60bd0e303f002a43b776f4bec0325208a07033e9c1a8`.
- Output ZIP SHA-256: `527b0cc94e40ff645b2a71168dcaad1ac9c3f06371658ea320e5e71852b17908` (377523 bytes).
- Version source archive SHA-256: `9b5a58a46182a7c905ecbfb0143121f2da787008429d72bc13ec4b4de6e420e8`.
- Version source tree SHA-256: `a5b10a92c867ff1a15511e37249d03c7161785da1ab678be6e2eabc2bcddb8e9`.
- Qualified framework distribution SHA-256: `7b68771ef7a7b6d92e9849eda0d97d8837590923873dc90a9bf21daa44c01fda`.

Exact artifact paths and hashes are in RESTORATION_RESULT.json; final run checks are in REPORT_PACKAGING_GATES_FINAL.json. Prior successful and failed attempt logs are retained in this directory.

## Decision and limitations

Reporting, packaging, standalone execution and repeat-run retention gates pass for the bounded A011-v0.4.1 pilot. This establishes the report/output binding for future authorized migrations; it does not migrate other falsifiers.

Migration remains PASS_GEOMETRY_ADAPTER, execution remains PASS_BOUNDED_GEOMETRY_SMOKE, and science remains UNRESOLVED_MISSING_PHYSICAL_INPUTS. Native parity is diagnostic only and cannot authorize physical claims. Physical gates G3/G4/G7/G8 were not executed, GPU G6 is disabled, and reveal G9 is deferred. The generic framework label BLIND denotes an unrevealed output here; this is not the complete private-target physical blind campaign.

Missing evidence includes calibrated physical length/SI scale, independent physical energies/gaps/relaxation/couplings, thermodynamic sampled state counts, held-out force/pressure mechanism evidence, and convergence beyond this two-level geometry smoke. No scientific status, dataset seal or blind/reveal commitment was promoted or changed. A054 and A065 were not modified. Their own unresolved admission conditions still prevent release of the following migration tranche. Scheduled remains PAUSED and is not automatically reactivated after these technical gates pass.
