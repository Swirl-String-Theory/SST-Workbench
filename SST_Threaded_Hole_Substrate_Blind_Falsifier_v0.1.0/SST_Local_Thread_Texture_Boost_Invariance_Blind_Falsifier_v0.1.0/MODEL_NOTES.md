# Model notes — source-generated local thread substrate

The targeted architecture is not a classical globally stationary ether. Around a source `a`, define a local texture/director field schematically by

\[
T_{ij}^{(a)}(\mathbf x)=W_a(r_a)n_i^{(a)}n_j^{(a)},
\qquad
\mathbf n^{(a)}=\frac{\mathbf x-\mathbf X_a}{|\mathbf x-\mathbf X_a|}.
\]

Multiple sources may superpose at the descriptor level,

\[
T_{ij}=\sum_a T_{ij}^{(a)}.
\]

The falsifier deliberately separates two questions:

- **boost nullity:** adding the same constant velocity to every filament point must not alter intrinsic evolution;
- **texture sensitivity:** a spatially varying source-generated field may alter intrinsic evolution only through an explicitly stated coupling.

The v0.1.0 radial and director couplings are controlled proxies. They are included to make the blind machinery executable now and to prevent the target effect from being inserted post hoc after looking at results.

A future canon gate should replace the proxy with a derived mapping

\[
(T_{ij},\nabla_kT_{ij},\rho_{\rm th},\nabla\rho_{\rm th})
\longmapsto
\delta\mathbf v_{\rm knot}
\]

without changing the blind commitment/scoring architecture.
