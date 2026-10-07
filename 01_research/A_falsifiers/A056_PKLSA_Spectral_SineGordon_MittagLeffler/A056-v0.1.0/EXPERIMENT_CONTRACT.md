# A056 experiment/provider contract

## Required provider object

One case is a phase field \(\varphi(t,s)\) sampled on a monotone rectangular grid. `phi` is dimensionless phase in radians. SI is preferred for `t` and `s`, but the blind fitting remains dimensionally valid in any declared consistent units.

## Derivatives

For interior time indices,

\[
\varphi_{tt}(t_i,s_j)\approx
\frac{\varphi_{i+1,j}-2\varphi_{i,j}+\varphi_{i-1,j}}{\Delta t^2}.
\]

For periodic carriers,

\[
\varphi_{ss}(t_i,s_j)\approx
\frac{\varphi_{i,j+1}-2\varphi_{i,j}+\varphi_{i,j-1}}{\Delta s^2},
\]

with periodic indexing. Open carriers exclude the two spatial endpoints.

The phase is unwrapped before differentiation. Grid nonuniformity above the configured tolerance fails G1 rather than silently applying a uniform-grid stencil.

## Optional ringdown

A provider may supply an independent non-negative, zero-baseline `ringdown` observable. If omitted, A056 derives a non-negative modal-energy proxy from the leading POD coordinates. Derived ringdown is flagged in the output and cannot be confused with an independently measured observable.

## Provenance

Every `.npz` input is SHA-256 hashed. The sidecar JSON may include an upstream source hash, solver version, timestep, mesh size and commit. A missing source group makes G5 unresolved but does not block case-level G3/G4 analysis.

## Blinding

The blind sidecar must use only an opaque case ID and source-group identifier. Human-readable topology/particle mappings belong in `PRIVATE/` and are opened only after blind outputs are frozen and hashed.
