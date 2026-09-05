# QM-readiness gates — v0.3.0

This extension does **not** assume that topological links are quantum states. It asks a narrower,
falsifiable question: does a selected classical link background admit a discrete sector catalogue,
a controlled reduced quadratic energy, a nondegenerate candidate two-form and a stable linearized
Hamiltonian spectrum?

## Q1 — discrete sector labels

The hard numerical input is the integer-locked Gauss-linking matrix. Component permutations that
preserve the rounded matrix and component lengths define a conservative automorphism proxy. All
circulation assignments \(\sigma_i=\pm1\) are quotiented by those permutations and global reversal.

For three-component links with every pairwise linking number zero, the ledger sets
`higher_linking_invariant_required=true`. It does not invent a Milnor invariant; that computation
remains an explicit unresolved dependency.

## Q2 — classical background candidate

At fixed \(\epsilon/D=0.10\), the suite combines the v0.2.1 normal rigid-motion residual with the
reduced gradient of an explicitly declared energy profile. A low residual is a candidate background,
not a proof of a finite-core stationary solution.

## Q3 — reduced quadratic stability

Normal deformations are expanded in low Fourier harmonics of a periodic rotation-minimizing frame.
Translations and rotations are projected out. Central differences give termwise gradients and
Hessians for:

- centerline length;
- bending integral;
- smooth tube-overlap penalty;
- regularized Neumann energy.

Each term is normalized by its baseline magnitude. Profile weights are configuration data, not canon.
A negative Hessian eigenvalue is a direct instability of that selected reduced closure.

## Q4 — candidate phase-space form

The Research-Track filament two-form is

\[
\Omega_{ab}=\sum_i\sigma_i\oint \hat{\mathbf t}_i\cdot
(\delta\mathbf X_a\times\delta\mathbf X_b)\,ds.
\]

The suite checks antisymmetry, rank, nullity and singular values. Full rank after gauge reduction is a
necessary readiness condition. It is not sufficient until this form is derived from the accepted SST
action and circulation normalization.

## Q5 — linearized Hamiltonian spectrum

For each energy profile,

\[
\Omega\,\dot{\mathbf q}=H\mathbf q,
\qquad
A=\Omega^{+}H.
\]

The eigenvalues of \(A\) are tested for real unstable parts, Hamiltonian \(\lambda\leftrightarrow-\lambda\)
pairing and positive dimensionless frequencies. Only frequency ratios are compared. Absolute
\(\hbar\omega\) energies are intentionally not produced.

## Readiness levels

0. not ready;
1. topological-sector ready;
2. classical-background candidate;
3. quadratic-stability candidate;
4. candidate-phase-space ready;
5. quantization-readiness candidate.

The gates are sequential. Level 5 means “a quantization method can now be attempted on this reduced
model,” not “quantum mechanics has been derived.”


## Preset semantics

- `qm_quick`: diagonal central-difference Hessian screen; readiness is capped at Q2.
- `qm_full`: complete off-diagonal Hessian for low harmonics through `mode_max=2`.
- `qm_max`: higher sampling and harmonic count; intended only after the closure survives `qm_full`.
