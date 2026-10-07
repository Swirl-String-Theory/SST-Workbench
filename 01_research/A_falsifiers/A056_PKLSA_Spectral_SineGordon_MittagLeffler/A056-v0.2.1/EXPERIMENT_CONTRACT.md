# A056 v0.2.1 experiment contract

## Scientific question

Does independently produced vortex-filament phase dynamics exhibit a reproducible effective Sine--Gordon restoring law, and does its relaxation exhibit reproducible fractional-memory behavior better described by a Mittag--Leffler law than by ordinary exponential alternatives?

## Non-negotiable provider boundary

A056 does **not** construct a phase field from a static knot curve after seeing the result. A real provider must supply `t`, `s`, and `phi(t,s)` plus a frozen `phase_definition_id`, perturbation ID, solver/provider version, carrier hash, upstream geometry hash, evidence class and replication group before A056 scores any model.

## Model family

Phase:

\[
H_W:\;\varphi_{tt}=a\varphi_{ss},\qquad
H_{KG}:\;\varphi_{tt}=a\varphi_{ss}-b\varphi,
\]

\[
H_D:\;\varphi_{tt}=a\varphi_{ss}-b\varphi-c\varphi^3,\qquad
H_{SG}:\;\varphi_{tt}=a\varphi_{ss}-b\sin\varphi.
\]

Relaxation:

\[
R_{\exp}=e^{-t/\tau},\quad
R_{\mathrm{stretch}}=e^{-(t/\tau)^\beta},\quad
R_{2\exp}=w e^{-t/\tau_1}+(1-w)e^{-t/\tau_2},
\]

\[
R_{ML}=E_{\alpha,1}\!\left[-(t/\tau)^\alpha\right].
\]

The exponential limit \(E_{1,1}(-t/\tau)=e^{-t/\tau}\) is explicitly protected by requiring the fitted fractional order to lie away from \(\alpha=1\).

## Framework lane order

`G0 provenance -> G1 admissibility -> G2 blind discovery -> G3 held-out confirmation -> G4 numerical certification -> G5 control replication + G5 physical cross-source replication -> G6 mechanism/physics -> REVEAL`.

A later physics gate cannot PASS unless its declared physical predecessors PASS.
