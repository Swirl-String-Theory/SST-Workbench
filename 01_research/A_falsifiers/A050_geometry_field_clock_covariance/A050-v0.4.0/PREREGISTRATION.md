# A050 v0.4.0 preregistration — fresh-holdout mechanism discrimination

## Frozen parents

- v0.3.0 verdict remains `REAL_GEOMETRY_MODAL_TRANSFER_NOT_REPRODUCED`.
- v0.3.2 diagnostic status remains `BRANCH_RETAINED_COHERENT_NONSTATIONARITY_SUPPORTED`.
- Parent v0.3.2 `blind_results.json` SHA-256: `c08aa9eb33960a4e2d21dc736967ff92382c6655344e10e07fa72d6dabe1d395`.

v0.4.0 may not revise either parent result.

## Fresh replication panel

The same five anonymous external baselines are reused, but the old v0.3.0/v0.3.2 holdouts are not used for mechanism replication. Five new transverse holdouts per primary baseline are generated after the mechanism rules are frozen, with seed `26010040` and target RMS perturbation `0.00125`. Source identity remains reveal-only. No numerical mode is fixed as a target.

A primary base must retain its branch in at least 4/5 fresh holdouts. At least 4/5 primary bases must satisfy this branch-retention prerequisite.

## Candidate mechanisms and gates

### H1 — smooth chirp
A coherent quadratic phase law with no significant reversal. Require quadratic \(R^2\ge0.85\), quadratic-over-linear \(\Delta\mathrm{BIC}\ge20\), quadratic NRMSE \(\le0.20\), relative start/end angular-rate change \(\ge0.25\), and zero significant sign reversals.

### H2 — two-tone beating
Model the selected complex coefficient as
\[
z(t)=c_0+A_1e^{i\omega_1t}+A_2e^{i\omega_2t}+\epsilon(t).
\]
Require two-tone-over-one-tone \(\Delta\mathrm{BIC}\ge20\), two-tone NRMSE \(\le0.35\), secondary/primary amplitude ratio \(\ge0.10\), at least 0.5 beat cycles over the horizon, envelope modulation depth \(\ge0.08\), envelope/beat angular-rate agreement within 35%, Reversal clustering at amplitude dips is reported as a secondary consistency diagnostic, not required for support.

### H3 — phase slip
Require at least one robust phase-increment outlier above both 0.35 rad and 8 robust-MAD scales, at least 75% of slip events at amplitude \(\le0.45\) of the median, and at least 50% of detected reversals matched to slip events when reversals exist.

### H4 — RPO candidate
Quotient the modal state by the selected branch spatial phase action \(C_m\to C_me^{-im\theta}\). Search lags 128–1024 steps. Require normalized median quotient distance \(\le0.30\), at least 24 state pairs, at least two estimated repeats, and group-phase-advance concentration \(\ge0.75\).

This establishes only `RPO_CANDIDATE`; it is not an RPO solution and does not permit Floquet/monodromy analysis.

### H5 — nonlinear amplitude–phase modulation
Require absolute lagged correlation between selected-mode amplitude and angular phase rate \(\ge0.55\), after simple two-tone beating and phase-slip signatures are excluded.

## Replication rule

For mechanism \(H_k\), a primary base is replicated only when:

1. the baseline supports \(H_k\);
2. at least 4/5 **fresh branch-retaining** holdouts support \(H_k\).

A mechanism passes campaign level only when at least 3/5 primary bases replicate it and the inherited anonymous source minima are satisfied: S01 >=2 replicated bases, S02 >=1, with both source groups confirmed.

## Falsifiable outcomes

- exactly one mechanism passes: mechanism-specific fresh-holdout replication;
- multiple mechanisms pass: `MULTIPLE_MECHANISMS_FRESH_HOLDOUT_REPLICATED`;
- branch retention passes but no mechanism passes: `COHERENT_NONSTATIONARITY_MECHANISM_UNRESOLVED`;
- fresh branch retention itself fails: `FRESH_HOLDOUT_BRANCH_RETENTION_FAILED`.

No mechanism status validates SST or identifies an absolute Kelvin-wave speed.
