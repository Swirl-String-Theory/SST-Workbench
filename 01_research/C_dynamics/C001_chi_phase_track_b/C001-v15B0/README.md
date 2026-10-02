# SST chi-phase package v15B.0

## Purpose

v15B.0 proposes the **single-modulus resolved core-envelope lemma** needed by
Track B as a canon-compatible local-core axiom. This patch keeps the status
conditional: the lemma is not yet derived from pre-existing SST filament
axioms alone.  Earlier packages established:

- v10B.1: the corrected GP/NLSE energy coefficient is `1/2`, not `1/4`;
- v11B.0: if the radial energy has coefficients `A,B,C`, the unit GP/NLSE
  equation follows when `A=B=C`;
- v12B.0: the algebraic tail justifies the `1/R^2 + 1/R^4 + ...` intercept;
- v13B.0: Track A and Track B are distinct selectors;
- v14B.0: a one-modulus isotropic envelope implies `A=B=C`.

v15B.0 does **not** close the full first-principles gate by itself. It records
the conditional local-core theorem:

```text
Single-modulus resolved envelope accepted
  -> A=B=C
  -> unit-vortex GP/NLSE radial equation.
```

Consequently the unit-vortex GP/NLSE radial equation is derived only within the
accepted single-modulus resolved-core sector, not from the full SST filament
canon without this extra local-core commitment.

## Canonized lemma

Let the resolved SST core envelope be represented locally by a single complex
order parameter

$$
\Psi(\rho,\theta)=F(\rho)e^{in\theta}.
$$

The canonical minimal transverse core-envelope energy is

$$
E_\perp[\Psi]
=
\kappa\int_{\mathbb R^2}
\left[
|\nabla\Psi|^2
+
\frac{1}{2\xi^2}(1-|\Psi|^2)^2
\right]d^2x .
$$

This is a **local resolved-core lemma**, not a claim about the external torsion
or causal radiation layer.

## Consequence

After polar reduction and scaling `rho = xi r`, the radial energy is

$$
E_\perp \propto
\int_0^\infty
\left[
F'^2r+n^2\frac{F^2}{r}+\frac12(F^2-1)^2r
\right]dr .
$$

Comparing with

$$
\mathcal L_r=A F'^2 r+B n^2\frac{F^2}{r}+\frac{C}{2}(F^2-1)^2r
$$

gives

$$
A=B=C.
$$

For `n=1`, the Euler--Lagrange equation becomes

$$
F''+\frac{F'}{r}-\frac{F}{r^2}+F(1-F^2)=0.
$$

## What this does *not* canonize

v15B.0 does **not** canonize:

- `alpha_ring = phi`;
- the exact legacy value `alpha_ring = 1.61`;
- a Lorentz clock derivation from the NLSE core alone;
- equality of internal core sound speed and the universal causal speed `c`.

It canonizes only the local one-modulus envelope lemma and its internal
`A=B=C` consequence.

## Files

- `DERIVATION_CANON_SINGLE_MODULUS_LEMMA.md` — derivation and status.
- `latex/CANON_LEMMA_v15B0_single_modulus_core_envelope.tex` — LaTeX block.
- `patches/SST_CANON-v0.8.15_v15B0.patch` — main-canon patch.
- `patches/SST_CANON-v0.8.15-research-track_v15B0.patch` — research-track patch.
- `patches/SST_CANON-v0.8.15_patched_v15B0.tex` — patched main canon.
- `patches/SST_CANON-v0.8.15-research-track_patched_v15B0.tex` — patched research track.
- `simulate_chi_phase_v15B0.py` — small consistency audit.

## Run

```bash
python simulate_chi_phase_v15B0.py
```

## Status

**CANON-COMPATIBLE CONDITIONAL LOCAL CORE LEMMA.**  The Track B GP/NLSE radial equation is
derived from this lemma if the single-modulus resolved envelope is accepted as
a local-core axiom. It is not yet derived from pre-existing SST filament axioms
alone.  Ring-constant numerics remain separate results
from v10B.1--v13B.0 and should be cited with their own numerical audit status.