# A056 v0.2.3 experiment contract

Real inputs are dynamic provider products, not static centerlines. Every case supplies `t`, `s`, `phi(t,s)` and optional zero-baseline ringdown data plus `A056-DYNAMIC-PROVIDER-4` metadata. The phase definition, perturbation protocol, solver/provider version and evidence provenance are frozen upstream before A056 model selection.

Phase competitors:

\[
\varphi_{tt}=a\varphi_{ss},\quad
\varphi_{tt}=a\varphi_{ss}-b\varphi,\quad
\varphi_{tt}=a\varphi_{ss}-b\varphi-c\varphi^3,\quad
\varphi_{tt}=a\varphi_{ss}-b\sin\varphi.
\]

Relaxation competitors:

\[
e^{-t/\tau},\qquad e^{-(t/\tau)^\beta},\qquad
w e^{-t/\tau_1}+(1-w)e^{-t/\tau_2},\qquad
E_{\alpha,1}[-(t/\tau)^\alpha].
\]

The v1.0.4 framework controls freeze, blindness, backend authority and replication semantics; A056 controls the science above.
