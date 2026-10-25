# CLOCK_ORIGIN_INDEPENDENT_OBSERVABLE_CAPTURE (P2.6 / P2.9)

Source: P0–P2.5 result `INDETERMINATE_NO_INDEPENDENT_PHASE_TARGET`. Do not open C006 / A031 / A021 / A030 / A035.

## Deliverables

1. **A029-v0.4.0** (copy-on-write from v0.3.0): raw modal timeseries capture, phase-blind return detector, nested PRED_M0–PRED_M3 against an independent target only.
2. **Generic schema** `SST_RAW_MODAL_TIMESERIES-1.0` so later C006/A031/A021 can emit the same observable without changing those packs now.
3. **A038-v0.5.1 only if** genuine geometry/mesh CAMPAIGN certs already exist. Overnight fixtures remain `BLOCKED_PROVENANCE`; do not bump A038 if they do not.

## Frozen naming (do not silently rename)

Skill \(S_M=1-\mathrm{CRMSE}_M/\mathrm{CRMSE}_{M0}\) requires a null comparator.

| Code name | Physical role | User note |
|-----------|---------------|-----------|
| PRED_M0 | leave-one-carrier-out circular mean | null, not advection |
| PRED_M1 | \(\mathrm{wrap}[-\omega_{\rm adv}(k_{\rm ref})\tau_{\rm ind}]\) | user's physical “M0 = advection” |
| PRED_M2 | \(\mathrm{wrap}[-(\omega_{\rm adv}+\omega_{\rm intrinsic})(k_{\rm ref})\tau_{\rm ind}]\) | user's “M1 = +intrinsic” |
| PRED_M3 | same at \(k_{\rm closed}\) | closed-loop / holonomy through \(k\); \(\Phi_{\rm hol,explicit}=0\) |

Report \(\Delta S_{10}=S_1-S_0\), \(\Delta S_{21}=S_2-S_1\), \(\Delta S_{32}=S_3-S_2\). Extra gate: PRED_M3 must beat PRED_M0 **and** PRED_M1 (advection), else the clock is advection-dominated even if \(S_3\ge 0.30\).

## Capture rule

Write \(a_m^{\rm raw}(t)=\langle q_m,\delta X(t)\rangle\) **before** demodulation, predicted-\(\omega\) bandpass, \(v_g\) windowing, synthetic packet fitting, or predicted phase correction. Spatial projector may be frozen (`independent_time_domain_given_frozen_spatial_mode`); never call that fully model-independent.

Return event: \(\tau_{\rm return,ind}=\arg\max_{\tau\in W_{\rm frozen}} C_{\rm env}(\tau)\). \(W_{\rm frozen}\) is protocol-fixed. \(L/|v_g|\) is a diagnostic only.

A029 has no time-stepper today. Do **not** synthesize \(a_m(t)\propto e^{\lambda t}\). If no raw series exists, emit `INDETERMINATE_NO_RAW_MODAL_TIMESERIES` and keep accounting from v0.3.0.

## Out of scope

C006-v0.3.0, A031-v0.3.0, A021-v0.5.0, A030-v0.3.0, A035-v0.4.0, A024/A016.
