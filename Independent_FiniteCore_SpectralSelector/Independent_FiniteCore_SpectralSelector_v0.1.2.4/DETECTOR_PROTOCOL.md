# Detector protocol v0.1.2.4

v0.1.2.4 changes candidate detection and physical-event de-duplication only. The finite-core operator, C++ kernel, Fourier projection, C4 leakage tests, branch tracking, and full numerical ladders are unchanged from v0.1.2.3.

## 1. Resolved growth floor

A sign change of the floating-point real part is not itself a physical marginal event. For each tracked branch define

\[
g(q)=|\operatorname{Re}\lambda(q)|.
\]

The preregistered effective detector floor is

\[
g_{\rm floor}=\max\!\left(10^{-8},\frac{\epsilon_{\rm machine}}{h/a}\right).
\]

A `fourier_sector_growth_transition` is emitted only when two adjacent accepted q samples straddle this floor:

\[
(g_a>g_{\rm floor})\oplus(g_b>g_{\rm floor}).
\]

The reported q is obtained by linear interpolation of `g=|Re(lambda)|` to the floor. A raw sign flip for which both endpoints satisfy `g <= g_floor` is counted in `rejected_subfloor_sign_flip_count` and cannot become a candidate.

Two above-floor endpoints are also not declared a resolved neutral transition at the current q step. This intentionally prefers a false negative over a branch-label or coarse-grid false positive.

## 2. Fixed |m| identity

A growth transition requires the same dominant `|m|` at both endpoints. Branches that change their dominant `|m|` across the bracket are rejected by the transition detector and counted diagnostically.

Branch-local `|lambda|` minima likewise require the same dominant `|m|` at the previous, central, and next q samples.

## 3. Conjugate / +/- eigenpair canonicalization

The real linear operator produces symmetry-related spectral partners. Before convergence clustering and the uniqueness gate, v0.1.2.4 identifies eigenvalues under

\[
z \sim z^* \sim -z \sim -z^*.
\]

For C4 sectors, residue sectors `r` and `-r mod 4` are also conjugate descriptions of the same physical `|m|` family. Thus sector 1 and sector 3 events may canonicalize to one physical event; sectors 0 and 2 are self-conjugate.

Canonicalized candidates report:

- `canonical_sectors`;
- `canonical_sector_class`;
- `canonical_branches`;
- `eigenpair_multiplicity`;
- `canonicalized_physical_event=true`.

This canonicalization never modifies the eigenvalues or operator. It only prevents expected spectral partners from making `gate_unique_candidate_per_case` fail.

## 4. Quick-run gate semantics

A reduced quick campaign does not contain the full `N=64,96,128`, shell `2,3`, and three-step FD ladders. Missing full-ladder gates are therefore emitted as

`"not_evaluated"`

rather than `false`. A full campaign still returns normal booleans. Promotion remains possible only when every required gate is exactly `true`.

## 5. Diagnostics

Each case now records `candidate_diagnostics`, including:

- raw real-part sign flips;
- rejected sub-floor sign flips;
- resolved growth-transition branch count;
- rejected dominant-|m| changes;
- raw candidate count;
- canonical candidate count;
- eigenpair duplicates removed.

These diagnostics are audit information and are not external target matching.
