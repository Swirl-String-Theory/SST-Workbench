# Fourier/C4 protocol

For `N` ring nodes, define the unitary low-mode basis

\[
U_{j,m}=N^{-1/2}e^{i m \theta_j},\qquad m=-M,\ldots,M.
\]

Normal and binormal amplitudes are retained separately, giving two coordinates per signed mode. For a real-space Jacobian `J`, the low-mode operator is

\[
A = U^\dagger J U.
\]

The low-mode projection residual is

\[
\epsilon_{\rm low}=\frac{\|JU-UA\|_F}{\|JU\|_F}.
\]

Because the periodic image lattice is cubic, the exact in-plane symmetry is C4. Modes therefore form residue sectors

\[
m \equiv r \pmod 4,\qquad r=0,1,2,3.
\]

The analysis permits coupling inside a residue sector and measures coupling outside it as `c4_symmetry_leakage`.

Each sector is diagonalized independently. Branches are propagated in q by maximizing phase-invariant eigenvector overlaps. Every sector eigenvector is assigned a dominant signed m and dominant |m| weight by summing its two polarization weights.

A candidate is not eligible if its branch is poorly tracked, its dominant mode weight is too low, its |m| is below 2, or the Fourier quality gates fail.


## v0.1.2.4 detector authority

Candidate transitions no longer use a raw sign change of `Re(lambda)`. Define

\[
g=|\operatorname{Re}\lambda|,\qquad g_{\rm floor}=\max\!\left(10^{-8},\frac{\epsilon_{\rm machine}}{h/a}\right).
\]

A resolved growth transition requires adjacent accepted q points on opposite sides of this floor. Sub-floor sign flips are rejected diagnostics. The same dominant `|m|` must be present on both sides of the bracket.

Before convergence clustering, eigenvalue partners are canonicalized under `z`, `z*`, `-z`, and `-z*`. C4 residue sectors `r` and `-r mod 4` are likewise treated as conjugate descriptions of one physical `|m|` family. See `DETECTOR_PROTOCOL.md`.
