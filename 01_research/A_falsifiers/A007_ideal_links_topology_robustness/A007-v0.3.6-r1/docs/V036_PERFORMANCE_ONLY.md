# v0.3.6 Performance-only release

v0.3.6 changes execution strategy only. It does **not** change the QM-readiness gates,
energy terms, Fourier cutoff definitions, finite-core parameters, finite-difference
stencils, reduced basis, or circulation-sector semantics from v0.3.5.1.

## Exact factorization of circulation sectors

The regularized Neumann contribution is

\[
E_N(\sigma,q)=\sigma^T C(q)\sigma.
\]

v0.3.5.1 finite-differenced this scalar separately for every one of the \(2^m\)
circulation assignments. v0.3.6 finite-differences the small coupling matrix \(C(q)\)
**once** and then contracts its baseline, gradient and Hessian with every sector:

\[
\partial_a E_N=\sigma^T(\partial_a C)\sigma,
\qquad
\partial_a\partial_b E_N=\sigma^T(\partial_a\partial_b C)\sigma.
\]

This is algebraically identical and preserves all sectors in the output.

For Borromean L6a4 (three components), the expensive Neumann finite-difference
quadrature is therefore reused across all eight circulation sectors.

## Geometric derivative cache

Length, bending and tube-repulsion do not depend on circulation signs. Both the coarse
and refined finite-difference derivative ledgers are now computed once per link/cutoff
and reused across all sectors. v0.3.5.1 already reused the coarse ledger, but recomputed
the refined ledger for each sector.

## Native tube repulsion

The exact existing diagnostic functional

\[
E_{rep}=\frac1{N_{pairs}}\sum_{pairs}
\operatorname{softplus}\!\left(\frac{D(1+\delta)-r_{ij}}{sD}\right)^2
\]

is implemented in C++17/OpenMP. The NumPy implementation remains the independent
reference. No sparse cutoff, KD-tree approximation or changed regularizer is introduced.

## Symmetric Neumann pair reuse

The coupling matrix is symmetric. Native and fallback backends now evaluate component
pairs only for \(i\le j\) and mirror the result. This removes redundant pair quadrature
while enforcing an exactly symmetric returned coupling matrix.

## Performance ledger

Every QM link JSON contains `performance_ledger`, including:

- reduced dimension;
- circulation-sector count;
- finite-difference evaluations per step;
- optimized geometric/Neumann evaluation counts;
- equivalent v0.3.5.1 counts;
- Neumann sector reuse factor.

## Explicit non-goals

v0.3.6 does not add GPU/CUDA, Torch autodiff, sparse repulsion or approximate neighbor
cutoffs. Those remain possible future accelerators but would require a separate parity
and/or numerical-method audit.
