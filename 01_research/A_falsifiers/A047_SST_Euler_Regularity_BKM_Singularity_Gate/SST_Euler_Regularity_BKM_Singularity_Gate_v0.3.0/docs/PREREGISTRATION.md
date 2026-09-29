# A047 v0.3.0 preregistration

## Primary falsification question

For E010/PKLSA-v0.3.1-qualified trefoil centerlines evolved as smooth finite-width vorticity tubes by the 3-D incompressible unforced Euler equations, does any tested centerline produce a **numerically valid, same-geometry resolution-convergent finite-time singularity candidate** under the frozen BKM screening heuristic?

## Upstream admission gate

The dataset is frozen by the local E010-v0.3.1 production `3_1` POC. Before dynamics, A047 requires the E010 source-contract, A001--A008 coverage, canonical-identity, identity-database, topology-database and trefoil-POC gates to pass. Default admission additionally excludes:

- E010 G1/G2/G3 literature-hard-gate failures;
- `BYTE_IDENTICAL_MIRROR_NOT_INDEPENDENT` and `MIRROR_NOT_INDEPENDENT` entries;
- recorded raw-byte and geometry duplicates.

Each admitted source is re-hashed and its decoded geometry must reproduce E010's `PKLSA-GEOMETRY-SHA256-v1` digest.

## Primary observable

\[
B(t)=\int_0^t \|\boldsymbol\omega(s)\|_{L^\infty}\,ds,
\qquad
M_\omega(t)=\|\boldsymbol\omega(t)\|_{L^\infty}.
\]

The late-window screening fit is

\[
M_\omega(t)^{-1}\approx a t+b,
\qquad
T_*=-b/a,
\]

only for \(a<0\). A single-run candidate requires \(R^2\ge0.98\) and \(T<T_*\le1.5T\). This is a numerical screening heuristic, not a sufficient mathematical blow-up criterion.

## Same-geometry convergence gate

Global escalation requires at least three numerically valid candidate runs at three distinct spatial resolutions **for the identical E010 carrier geometry** and a relative spread of estimated \(T_*\) below 10%. Different carriers, source families, or independence groups can never be pooled to satisfy this gate.

## Numerical-validity gates

The selected config freezes its own energy threshold. BASIC uses

\[
\frac{|E(T)-E(0)|}{|E(0)|}<10^{-4},
\qquad
\max_t\|\nabla\cdot\mathbf u\|_{\rm RMS}<10^{-10}.
\]

The certification template tightens the energy-drift threshold to \(5\times10^{-5}\).

## Blindness

BLIND contains only salted geometry/case IDs, salted E010 independence-group IDs, grid/time metadata, canonical-coordinate hashes and dynamical diagnostics. Carrier IDs, source-family names, source paths, catalog IDs, independence-group names, lineage/method labels and SST canonical constants are REVEALED only after the blind assessment is frozen.

## Scope limits

The solver uses a periodic pseudo-spectral cube rather than the compactly supported \(\mathbb R^3\) construction of the Euler blow-up preprint. E010's geometry qualification is an upstream data-integrity condition, not evidence of Euler/Biot--Savart stability. A047's finite-window numerical gate is likewise not a proof of regularity or singularity.
