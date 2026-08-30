# Scientific audit — Trefoil Mega Falsifier v0.2.0

Audit date: 2026-08-30. Evidence source: local code, frozen configuration and stored JSON outputs in the v0.2.0 package. Conversation prose is treated as a claim, not as evidence.

## Classification vocabulary

- **VERIFIED** — directly supported by locally inspectable artifacts.
- **SUPPORTED** — evidence points in this direction but is incomplete or not independently replicated.
- **INDETERMINATE** — the relevant physics question was not decisively tested.
- **CONTRADICTED** — the stored artifacts disagree with the claim.
- **UNVERIFIABLE** — no adequate artifact was available in the audit scope.

Numerical and physics status are independent. A passing test suite, native parity check or synthetic smoke never counts as a physics PASS.

## Artifact-level findings

| Claim | Classification | Artifact finding | Strongest defensible conclusion |
|---|---|---|---|
| v0.1.1 found no near-RPO | CONTRADICTED | All five S40 trajectories stopped before the return window; S50/S60 had zero rows | RPO existence was numerically untested |
| v0.2.0 BASIC was source-stratified over three source families | CONTRADICTED | prepare_summary.json reports three discovered files but one group with candidates; link_0.3.1_final.txt and link_6.3.1_final.txt were admitted by the regex and then entirely rejected | The real BASIC result is a one-source search |
| v0.2.0 produced mesh-gauge-certified blind seeds | CONTRADICTED | S37 reports 0/8 qualified; best final-shape discrepancy is 0.035943229463292516 against the frozen 0.035 gate | No real blind candidate entered S40 |
| R557 long-run regression passed T=0.9 and T=1.2 | VERIFIED | VALIDATION.md records completed regression runs and mesh/physical ratios | The new controller improves numerical coverage for one previously selected geometry |
| R557 regression establishes recurrence or stability | CONTRADICTED | The regression is non-blind and no RPO/Floquet result follows from it | It is numerical regression evidence only |
| Full synthetic chain validates the workflow | VERIFIED | The package documents a permissive three-source smoke reaching S70 | Code paths are exercised; this is not SST evidence |
| v0.2.0 chain summary correctly represented S37 failure | CONTRADICTED | CHAIN_CORE_ROBUST_MESH_CERTIFIED__RPO_NOT_TESTABLE_NUMERICALLY was emitted while S37 had zero qualified seeds | Chain-verdict precedence contained an epistemic labeling bug |
| S40 and S50 evaluated one discretized flow map | CONTRADICTED | S40 used global_volume plus tangential mesh feedback; S50 replayed fixed core without mesh feedback | The projected monodromy was not the derivative of the searched S40 map |
| S60 established causality | CONTRADICTED | S60 used lag discovery plus held-out linear prediction, without intervention or ablation | At most a predictive-specificity candidate can be claimed |

## Locked interpretation of the real v0.2.0 BASIC run

1. S20–S35 identify a tight, one-source cluster that is numerically consistent on the implemented short-horizon diagnostics.
2. S32 is machine-floor limited for the selected candidates; its stored observed order of zero is not a physical or numerical order estimate.
3. S37 rejects all eight candidates. The miss of the best candidate is small but remains a FAIL under the frozen threshold and must not be tuned away post hoc.
4. S40, S50 and S60 were not run on a certified blind candidate. No recurrence, Floquet-stability or mechanism conclusion follows.
5. All claims remain limited to the regularized filament/finite-core surrogate.

## Remediation traceability

v0.2.1 addresses each discrepancy with full-name source filtering, a minimum source-diversity gate, explicit convergence modes, direct spatial trajectory comparison, a shared dynamics contract, local return-quality metrics, non-causal S60 terminology, sealed private artifacts and separate numerics/physics verdicts.
