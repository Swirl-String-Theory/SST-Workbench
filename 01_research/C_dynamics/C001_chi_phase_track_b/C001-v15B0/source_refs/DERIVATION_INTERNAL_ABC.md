# Derivation: internal SST condition for `A=B=C`

## 1. Starting point

Let the resolved SST core envelope be represented by a compact complex order parameter

$$ 
\Psi(\rho,\theta)=F(\rho)e^{in\theta},
 $$ 

where `F` is the dimensionless core-amplitude/depletion profile and `n` is the integer winding number.

The minimal isotropic core-envelope energy in the transverse plane is

$$ 
E_\perp[\Psi]
=
\kappa\int_{\mathbb R^2}
\left[
|\nabla\Psi|^2
+\frac{1}{2\xi^2}(1-|\Psi|^2)^2
\right]d^2x.
 $$ 

Here `κ` is the single core stiffness and `ξ` is the healing/core-envelope length. The important assumption is **single isotropic stiffness**: amplitude gradients and phase gradients use the same transverse metric and the same coefficient.

## 2. Polar reduction

In polar coordinates,

$$ 
|\nabla\Psi|^2
=
\left(\frac{dF}{d\rho}\right)^2
+\frac{n^2F^2}{\rho^2}.
 $$ 

Set

$$ 
\rho=\xi r.
 $$ 

Then, up to the common factor \(2\pi\kappa\),

$$ 
E_\perp
\propto
\int_0^\infty
\left[
F'^2 r
+n^2\frac{F^2}{r}
+\frac12(F^2-1)^2r
\right]dr.
 $$ 

Comparing with

$$ 
\mathcal L_r
=
A F'^2 r
+B n^2\frac{F^2}{r}
+\frac{C}{2}(F^2-1)^2r,
 $$ 

we obtain

$$ 
\boxed{A=B=C.}
 $$ 

## 3. Euler--Lagrange equation

For

$$ 
\mathcal L_r
=
A F'^2 r
+B n^2\frac{F^2}{r}
+\frac{C}{2}(F^2-1)^2r,
 $$ 

the Euler--Lagrange equation is

$$ 
\frac{d}{dr}\left(2ArF'\right)
-\left(2Bn^2\frac{F}{r}+2CF(F^2-1)r\right)=0.
 $$ 

Dividing by \(2Ar\) gives

$$ 
F''+\frac{F'}{r}
-\frac{B}{A}n^2\frac{F}{r^2}
+\frac{C}{A}F(1-F^2)=0.
 $$ 

For the unit vortex sector

$$ 
n=1,
\qquad
A=B=C,
 $$ 

this reduces to

$$ 
\boxed{
F''+\frac{F'}{r}-\frac{F}{r^2}+F(1-F^2)=0.
}
 $$ 

This is exactly the GP/NLSE vortex ODE used in v10B.1--v12B.0.

## 4. Factor-2 consistency rule

The energy potential term must be

$$ 
\frac12(F^2-1)^2r.
 $$ 

If instead the energy contains

$$ 
\frac14(F^2-1)^2r,
 $$ 

then in the notation above \(C=1/2\), so the ODE would contain

$$ 
\frac12F(1-F^2),
 $$ 

not the unit coefficient \(F(1-F^2)\). This is exactly why v10B.0 was inconsistent and v10B.1 corrected the interaction term.

## 5. Canon gate

The result is not an unconditional canon theorem unless the canon accepts the single-isotropic-core-envelope lemma:

$$ 
\boxed{
\text{Resolved SST core envelope has one isotropic stiffness modulus.}
}
 $$ 

Once that lemma is accepted, `A=B=C` is no longer an imported GP/NLSE assumption. It follows from the SST core-envelope energy itself.