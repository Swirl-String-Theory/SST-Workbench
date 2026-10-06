# Preregistered hypotheses

## H0 — persistent trefoil

Initial state: one-component `3_1`.

Mandatory interaction claim:

\[
3_1 \xrightarrow{\mathcal P} 3_1,
\]

with no reconnection/topology-changing event. Interaction may excite modes, but the topology and one-component identity survive.

## H1 — persistent Hopf with mode locking

Initial state: two-component `L2a1`, \(|Lk|\approx1\).

Mandatory claim:

\[
L2a1 \xrightarrow{\mathcal P} L2a1,
\]

while the independently defined phase-lock statistic increases and remains locked during the post-pulse window.

The lock statistic follows the A051-compatible order parameter

\[
R_{12}=\left|\frac{\sum_t w_t e^{i\phi_{12}(t)}}{\sum_t w_t}\right|.
\]

A static geometry label is not a phase measurement. If no independent material/modal phase is supplied, H1 is `INDETERMINATE_NO_PHASE_OBSERVABLE`.

## H2 — Hopf to Solomon topological transition

Initial state: `L2a1` with \(|Lk|\approx1\).

Claim:

\[
L2a1 \xrightarrow{\mathcal P} L4a1,
\qquad |Lk|:1\rightarrow2.
\]

Mandatory safeguards:

- finite-core/reconnection-capable declared producer;
- local target-blind reconnection rule;
- event temporally associated with interaction rather than sham control;
- stable post-event \(|Lk|\approx2\);
- convergence and source robustness;
- accounting residuals within declared tolerance.

## H3 — transient compound

Initial state: `3_1`.

During interaction, a multi-component state must appear with a robust `L2a1`- or `L4a1`-like mutual-linking signature, followed by return to the declared one-component electron sector after the interaction window.

This is intentionally stricter than merely observing fragmentation. A transient component count >1 without quantified mutual linking is insufficient.

## Tournament outcome

The scientific result is a set-valued verdict:

\[
\mathcal S=\{H_i:\text{all mandatory gates for }H_i\text{ pass}\}.
\]

- \(|\mathcal S|=0\): all tested hypotheses falsified/unsupported in the tested domain.
- \(|\mathcal S|=1\): unique survivor in the tested domain.
- \(|\mathcal S|>1\): experiment does not discriminate sufficiently.

No scalar score is permitted to turn a failed mandatory gate into a winner.
