# Blind preregistration — v0.1.1

## Generic closure test

Exact closure is

\[
k_0L+m\Theta_B=2\pi n.
\]

The matched control is symmetric:

\[
k_\pm L+m\Theta_B=2\pi(n\pm\delta).
\]

Its growth metric is

\[
g_{\rm sym}=\tfrac12[g(k_-)+g(k_+)].
\]

This is fixed before blind execution. The first-order local dispersion slope cancels in the symmetric average.

### Integrity rules

- closure votes use only pairs with `closed_mode_valid = true` **and** `control_mode_valid = true`;
- neutral/neutral pairs with both positive-growth metrics below `neutral_growth_epsilon` are ties and cannot create a ratio vote;
- carrier statistics use only both-valid, non-neutral pairs;
- measured-delay statistics use only valid CLOSED modes with a successful wave-packet return;
- no individual favorable point can override a failed carrier-cluster gate.

## Self-generated delay

No delay parameter is supplied. The eigenbranch gives

\[
v_g=d\omega/dk,\qquad \tau_g=L/|v_g|,
\]

and a packet return independently measures \(\tau_{ret}\).

## m=1 confirmatory Swirl-Clock gate

The prior v0.1.0 extended run discovered post hoc a candidate \(m=1\) phase optimum

\[
\boxed{\phi_\star=2.72\ \mathrm{rad}}.
\]

v0.1.1 freezes this before new data. It is **not used in dynamics**.

Primary new carriers:

`TORUS_T2_5`, `TORUS_T2_7`, `TORUS_T3_4`, `TORUS_T3_5`, `TWIST_4_1`, `TWIST_7_2`.

For each carrier, over both-valid/non-neutral \(m=1\) rows, fit

\[
y=a+b\cos(\phi_{loop}-\phi_\star).
\]

Prediction:

\[
\boxed{b<0.}
\]

The confirmatory phase gate requires at least six carrier votes and one-sided exact sign-test \(p\le0.05\).

The corresponding `m=2` campaign is a negative/control branch: the \(m=1\) target should not reproduce as a universal \(m=2\) law.

## Generic aggregate thresholds

- finite-core CLOSED-mode valid fraction: preset-specific, normally >= 0.60;
- median valid-only group-delay vs wave-packet-return relative error <= 0.30;
- carrier-cluster exact sign test for CLOSED lower growth: one-sided p <= 0.05;
- carrier-cluster median CLOSED/symmetric-control growth ratio <= 0.90;
- leave-one-carrier-out circular phase-growth CV \(R^2\) >= 0.15;
- grouped phase permutation p <= 0.05.
