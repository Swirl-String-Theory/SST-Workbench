# Derivation: conditional single-modulus core-envelope lemma

## 1. Conditional local-core lemma

The local resolved SST core is represented by a single complex envelope field

$$ 
\Psi(\rho,\theta)=F(\rho)e^{in\theta}.
 $$ 

The proposed canonical transverse core energy is

$$ 
E_\perp[\Psi]
=
\kappa\int_{\mathbb R^2}
\left[
|\nabla\Psi|^2
+\frac{1}{2\xi^2}(1-|\Psi|^2)^2
\right]d^2x.
 $$ 

The words "single-modulus" mean that radial amplitude gradients and azimuthal
phase gradients share the same coefficient because they are components of the
same Euclidean transverse gradient norm \(|\nabla\Psi|^2\).  The depletion term
uses the same envelope scale after nondimensionalization.

## 2. Polar reduction

For the unit-winding ansatz generalized to integer winding \(n\),

$$ 
|\nabla\Psi|^2
=
\left(\frac{dF}{d\rho}\right)^2+\frac{n^2F^2}{\rho^2}.
 $$ 

With \(d^2x=\rho d\rho d\theta\) and \(\rho=\xi r\), the energy becomes, up to
a common factor \(2\pi\kappa\),

$$ 
E_\perp\propto
\int_0^\infty
\left[
F'^2r+n^2\frac{F^2}{r}+\frac12(F^2-1)^2r
\right]dr.
 $$ 

Comparing to the generic radial density

$$ 
\mathcal L_r=A F'^2 r+B n^2\frac{F^2}{r}+\frac{C}{2}(F^2-1)^2r
 $$ 

gives immediately

$$ 
A=B=C.
 $$ 

## 3. Euler--Lagrange equation

For the generic radial density,

$$ 
\frac{d}{dr}(2ArF')-
\left(2Bn^2\frac{F}{r}+2CF(F^2-1)r\right)=0.
 $$ 

Dividing by \(2Ar\),

$$ 
F''+\frac{F'}{r}-\frac{B}{A}n^2\frac{F}{r^2}
+\frac{C}{A}F(1-F^2)=0.
 $$ 

The conditional single-modulus lemma sets \(A=B=C\). For the single-quantum core
\(n=1\),

$$ 
F''+\frac{F'}{r}-\frac{F}{r^2}+F(1-F^2)=0.
 $$ 

## 4. Factor rule

The depletion term must be

$$ 
\frac12(F^2-1)^2r.
 $$ 

A coefficient \(1/4\) would vary to \(\frac12F(1-F^2)\), not to the unit
coefficient in the canonized GP/NLSE radial equation.  This is why the v10B.0
energy convention is rejected and the v10B.1 convention is retained.

## 5. Status

This file records the local core-envelope lemma and the resulting `A=B=C`
identity as a conditional theorem.  It does not canonize any exact numerical identification of
\(\alpha_{\rm ring}\) with \(1.61\) or \(\varphi\).