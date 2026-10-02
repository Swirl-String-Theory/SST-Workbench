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
