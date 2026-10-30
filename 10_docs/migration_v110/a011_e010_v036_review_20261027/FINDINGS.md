# A011 log review and E010-v0.3.6 suitability

Review date: 2026-10-27. Scope: read-only inspection, current A011 SELFTEST, downloaded E010 metadata and three existing geometry samples. No migration, scientific campaign, status promotion or queue change was performed.

## A011 actual log and status

The last published geometry adapter run is 20261026T184203243717Z-0d021239, A011-v0.4.1. Its log reports 39 passed in 1.01s, migration PASS_GEOMETRY_ADAPTER, execution PASS_BOUNDED_GEOMETRY_SMOKE and science UNRESOLVED_MISSING_PHYSICAL_INPUTS. RUN_SUMMARY.json has errors=[] and explicitly states that no full physical campaign was run.

G0/G1/G2 passed for framework/protocol, exact admitted geometry and finite geometry diagnostics. G5 passed native/reference geometry parity but has DIAGNOSTIC_ONLY qualification and allows_dependent_claim=false. The maximum recorded velocity difference is 2.220446049250313e-16; writhe and distance differences are zero in the six comparisons. G3/G4/G7/G8 are NOT_RUN_PREREQUISITE and NOT_EXECUTED; GPU G6 is disabled and reveal G9 deferred.

The current manual run_all.cmd SELFTEST exited 0, with 39 passed in 1.18s. Exact new stdout is retained in A011_SELFTEST_CURRENT.log. The stored published PDF/ZIP hashes, version source inventory, frozen protocol, qualified framework and the three original admitted geometry sources were also reverified. The historical geometric run was not rerun or replaced.

## What the current adapter actually implements

framework_v110.py explicitly binds G3, G4, G7 and G8 to unavailable(), which raises GateInputsUnavailable. The adapter only accepts GEOMETRY_AND_IMPLEMENTATION_DIAGNOSTIC_ONLY and the frozen three-source plan (0_1, 3_1, 4_1, N=64/128). Changing a source file or substituting a newer dataset would be rejected by its pins; even a newly accepted geometry does not implement the missing physical evaluators.

The current registered missing evidence is:

- Calibrated physical length and SI source scale.
- Independent physical energy spectra/gaps and relaxation/couplings.
- Independent thermodynamic sampled state counts.
- Held-out force/pressure and mechanism validation.
- Spatial, temporal, solver and regularization convergence beyond the two-level geometry smoke.

The inherited full campaign code expects observable records such as modes, amplitude_scan, encounters, convergence and energy_ledger; optional thermodynamic/force claims require their corresponding state-count and held-out records. Initial curve coordinates do not supply those records automatically. Passing synthetic unit tests does not supply physical evidence.

## E010-v0.3.6 inspected contents

The local version/output folders existed but were empty at inspection. The actual release was found in the user's Google Drive. Copies were downloaded only to this review folder, under the existing standing source-admission authorization.

The core archive SHA-256 matches RELEASE_ARCHIVES.sha256: a56ec7b238f949658bcf8ed657c204cf2a35688fe03529db8e85ce8b732c44c5. The first knot shard SHA-256 also matches: 20db6defecb0e21820fb8d861bdf09766c398412ba3aaf1522c9323f6bee4546. All five core output metadata files match their internal manifest entries. Source/core common code files are identical; the sole common-file difference is a README paragraph describing single-archive versus split-shard delivery. Both originals and the exact diff are retained.

BUILD_SUMMARY, FAMILY_INDEX and DYNAMICS_PENDING establish:

- Status GEOMETRY_ONLY_DYNAMICS_NOT_RUN; research_only=true; production_admission=false.
- 24 knot embedding families and six three-component link families, 121 B0 values.
- 3630 nominal and 3630 perturbed realizations; 10164 XYZ coordinate files; 1024 points per component.
- All 54450 listed scenarios have gate=PENDING and dynamics_backend=NOT_RUN (checked across every scenario).
- One analytic source group; generated torus coordinates are not imported native KnotPlot coordinates or independent empirical replications.
- All listed seed components have qualified_for_active_atlas=false and all seeds have finite_core_qualified=false.

The three inspected T_2_3 seeds at B0=0.02, 0.10 and 0.32 each have a matching raw hash, 1024 finite XYZ points and a recorded canonical parsed-geometry hash. Their dynamic stability remains NOT_TESTED. These checks qualify the inspection of those payloads, not physical stability or admission to A011's frozen production contract. Only core/source and KNOTS_01 were downloaded; the other six coordinate shards were not fully audited.

An additional binding issue is preserved in REVIEW.json: configs/family_registry_overlay.json still identifies v0.3.5-DEVELOPMENT and points to the v0.3.5 output index. A future v0.3.6 intake must use an explicitly versioned derived binding to the correct v0.3.6 index. Do not rewrite the historical archive or manifests to hide this reference.

## Decision and concrete next work

The v0.3.6 seeds can improve geometry/parser/native-kernel stress coverage through controlled aspect-ratio and perturbation cases. They do not close the existing A011 physical gates because this release has no executed dynamics, calibrated spectrum, thermodynamic sampled state counts or independent held-out mechanism evidence.

A suitable next implementation tranche would:

1. Preserve A011-v0.4.1 and its results; create a separately authorized successor for changed input semantics (for example v0.5.0).
2. Add an explicit research-geometry intake for selected v0.3.6 seed IDs, raw/parsed hashes, correct index binding, analytic provenance and single-/multi-component handling. Keep the original pilot as the retained baseline and do not treat the six three-component links as single-component curves.
3. Run bounded geometry/parity controls with the inherited tolerances and a preregistered convergence plan; label them geometry-only.
4. For real scientific progress, define the physical observable contract for the chosen A011 claim and implement the appropriate G3/G4/G7/G8 evaluators instead of unavailable(). Acquire traceable solver/measurement outputs with the required scales, uncertainty, convergence and independence; keep unsupported claims unresolved.

No source-consent question is needed for local/Drive files. Dataset/capability qualification and execution scope remain distinct from that consent. Machine-readable evidence and exact sample hashes are in REVIEW.json; new SELFTEST logs and downloaded originals are retained alongside it.
