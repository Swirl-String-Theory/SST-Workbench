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
