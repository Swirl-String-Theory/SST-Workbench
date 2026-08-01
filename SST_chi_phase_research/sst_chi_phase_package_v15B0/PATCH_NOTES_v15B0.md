# Patch notes — SST Canon v0.8.15, v15B.0

## Intent

Canonize the new local core-envelope lemma needed to close the Track B
GP/NLSE gate:

$$ 
E_\perp[\Psi]
=
\kappa\int_{\mathbb R^2}
\left[
|\nabla\Psi|^2+\frac{1}{2\xi^2}(1-|\Psi|^2)^2
\right]d^2x.
 $$ 

## Main-canon change

Adds a new subsection after the Two-Speed Discipline section:

```tex
\subsection{Canonical Single-Modulus Core-Envelope Lemma}
```

This promotes the one-modulus local internal core-envelope model to a canon
lemma and derives:

$$ 
A=B=C,
 $$ 

and for \(n=1\):

$$ 
F''+F'/r-F/r^2+F(1-F^2)=0.
 $$ 

## Research-track change

Adds a bridge subsection in the Core--Torsion Impedance Matching section stating
that the GP/NLSE Track B core equation is now canon-derived from the main-canon
local core-envelope lemma.

## Explicit non-claims

This patch does **not** canonize:

- \(\alpha_{\rm ring}=1.61\) exactly;
- \(\alpha_{\rm ring}=\varphi\);
- any identification of \(\alpha_{\rm ring}\) with the fine-structure constant;
- a Lorentz Swirl-Clock derivation from the NLSE core alone.

The core--torsion impedance gate remains open.