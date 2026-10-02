# Methodology and falsification ledger

## A. Matrix convention

For active constraints \(g_j(X)\), the native core uses columns

\[
A_j=\nabla_X g_j.
\]

For inferred struts,

\[
g_j=\frac12 d_j,
\]

with closest points interpolated on the two polygon segments. For kinks,

\[
g_j=\operatorname{MinRad}_j,
\]

and its local 9-coordinate gradient is evaluated by centered finite differences.

For the built-in length energy,

\[
b=\nabla_X L,
\qquad
A\Lambda\simeq b,
\qquad \Lambda\ge0.
\]

This corresponds to the first-order balance \(-\nabla L+A\Lambda=0\).

## B. Tests and decision status

| Test | Quantity | Decisive status |
|---|---|---|
| Global KKT | \(\chi_{\rm KKT}\) | decisive for first-order length criticality under the declared active set |
| Local closure | vertex-wise \(\|A\Lambda-b\|\) | decisive consistency test for the same first-order model |
| Right nullspace | \(\dim\ker A\) | exact numerical rank diagnostic at preregistered tolerance |
| Positive self-stress | \(\ker A\cap\mathbb R_+^M\) | decisive existence test for normalized positive self-stress at that tolerance |
| Left nullspace | \(\dim\ker A^T\) | contact-network diagnostic; full-mechanics interpretation guarded |
| Smallest positive singular value | \(\sigma_{\min}^+\) | conditioning diagnostic; not a Kairos proof |
| Contact-map convergence | Hausdorff distance on normalized arclength pairs | resolution gate |
| Strict reciprocal complex | supplied dual-cell incidence | optional; nonexistence alone is not mechanical falsification |
| Force-area mapping | \(A^\star=F/\Pi_\star\) | physical only with preregistered forces in N |

## C. Blindness

The runner sees only blinded case and group IDs, resolution, geometry status, methodological source role, and preregistered numerical scales. Physical labels are kept in the private key until the run is complete.

## D. Minimal production campaign

For each knot/link family:

1. at least three mesh resolutions;
2. preferably at least five independent relaxed starts at the highest two resolutions;
3. original constrained audit geometry retained;
4. explicit strut/kink sidecars and solver multipliers retained when possible;
5. no thresholds altered after any physical label is unblinded;
6. exact hashes for every geometry and sidecar.

The strongest falsifier is not a single bad rank. It is non-convergence or reproducible incompatibility of the active contact measure, KKT balance, positive self-stress structure, or singular spectrum under matched topology, thickness convention, energy, and resolution refinement.

## E. v0.2.0 shared-final adapter

The `KnotPlot/knots/final` export is treated as a geometry-plus-metadata pair. For links, `vertices_per_component` from the paired metrics JSON is used to split components; blank lines in the XYZ/TXT file are not required.

When explicit strut sidecars are unavailable, candidate contacts are reconstructed with the preregistered two-sided shell

\[
2a(1-\varepsilon_c)\le d_{ij}\le 2a(1+\varepsilon_c),
\]

with baseline \(\varepsilon_c=10^{-4}\). The extended campaign reports sensitivity to a frozen tolerance ladder. The inferred active set is therefore an adapter estimate, not a claim that the original Ridgerunner strut list has been exactly recovered.

## F. Geometry-QC refusal

A shared-final geometry whose recorded Ridgerunner residual exceeds the preregistered threshold is still hashed, blinded, loaded, and geometrically inventoried. Its equilibrium/rank/self-stress interpretation is refused rather than counted as an SST failure. The default threshold is

\[
R_{\mathrm{RR}}\le 0.05.
\]

This separates optimizer non-convergence from physical falsification.

## G. Maxwell small-disfigurement gate

For cases with baseline

\[
\sigma_{\min}^{+}/\sigma_{\max}<10^{-4},
\]

extended mode applies deterministic blinded coordinate perturbations of frozen amplitudes expressed as fractions of the declared tube radius. Rank, contact count, \(\chi_{\mathrm{KKT}}\), and the singular ratio are recomputed. This directly operationalizes Maxwell's warning that a small disfigurement can drive very large force changes or loosen a frame, while keeping the result a numerical conditioning diagnostic rather than a dynamical Kairos claim.
