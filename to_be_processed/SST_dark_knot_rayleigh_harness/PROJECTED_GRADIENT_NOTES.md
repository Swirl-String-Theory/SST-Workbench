# Projected-gradient integration notes

The final Ridgerunner-level evolution should minimize

\[
E_\Omega(V)=E_{\rm rope}(V)+\eta_R\sum_jw_j[\Phi_R(r_j;V)-4\Omega^2]^2
+\chi_R\sum_jw_j\Phi_R(r_j;V)
\]

subject to fixed thickness.

The projection step should follow the standard active-constraint structure:

\[
-\nabla E_\Omega = (-\nabla E_\Omega)_R + (-\nabla E_\Omega)_I,
\]

where

\[
(-\nabla E_\Omega)_R=A\Lambda,\qquad \Lambda\ge0,
\]

and the constrained motion is

\[
\dot V=(-\nabla E_\Omega)_I=-\nabla E_\Omega-A\Lambda.
\]

`A` is the rigidity matrix with active strut and kink gradients as columns. The NNLS solve is

\[
\min_{\Lambda\ge0}\|A\Lambda-(-\nabla E_\Omega)\|.
\]

## Implementation stages

1. Keep the present package as the **diagnostic audit layer**.
2. Replace `active_constraint_summary()` with true Ridgerunner `Strut(V)` and `Kink(V)` import/export.
3. Add exact columns:
   - `-grad d(p,q)/2` for struts,
   - `-grad MinRad^\pm(v_i)` for kinks.
4. Add sparse NNLS for `A Lambda ~= -grad E`.
5. Use finite-difference checks on `grad E_Rayleigh` only after `epsilon_BS`, `h`, `Delta r` are frozen.
6. Run first with `chi_R=0`, then activate small `chi_R != 0` for `3_1`/`4_1` contrast.

## Status tag

This file is Research Track scaffolding. It is intentionally conservative: the current runnable code does not claim to be a full ropelength minimizer.
