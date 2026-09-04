# CANON status: v12B.0

## Status

**Strong Research Track / asymptotic-extraction support.**  
Not locked CANON.

## What is derived here

v12B.0 derives and numerically validates the GP/NLSE algebraic far-field tail:

$$ 
F(r)=1-\frac{1}{2r^2}-\frac{9}{8r^4}-\frac{161}{16r^6}+\cdots .
 $$ 

For the corrected GP/NLSE energy integrand

$$ 
I(r)=\frac{F^2}{r}+(F')^2r+\frac12(F^2-1)^2r,
 $$ 

it derives

$$ 
C_\infty-C(R)
=
-\frac{1}{4R^2}+\frac{1}{4R^4}+\frac{11}{6R^6}+\cdots .
 $$ 

This justifies the algebraic extrapolation law used to extract

$$ 
\alpha_{\rm ring}^{\rm GP}=2-C_\infty.
 $$ 

## What is not derived here

v12B.0 does **not** prove the SST-internal stiffness lock

$$ 
A=B=C.
 $$ 

That lock remains the gate between derived-conditional and locked-CANON.

## Canon-safe statement

$$ 
\boxed{
\text{Assuming the SST core-envelope reduces to the GP/NLSE unit vortex,}
\text{ the finite-radius extraction of }\alpha_{\rm ring}^{\rm GP}
\text{ is governed by an algebraic }1/R^2+1/R^4+\cdots\text{ tail.}
}
 $$ 

## Notation guard

Use \(\alpha_{\rm ring}\) and \(\beta_{\rm ring}\). Do not conflate these vortex-ring constants with the fine-structure/shielding-gate \(\alpha\), nor with the Regge slope \(\alpha'\).