# Derivation note: SST core envelope to GP/NLSE vortex equation

## 1. Core-envelope ansatz

Let the internal SST core envelope be represented by a dimensionless complex field

$$ 
\Psi(r,\theta)=F(r)e^{in\theta}.
 $$ 

This is not introduced as a new fundamental field. In this Track B interpretation it is an effective internal envelope for the resolved vortex core.

## 2. Most economical radial energy

For an isotropic internal core envelope, the minimal radial energy with phase winding and density depletion is

$$ 
\mathcal L_r
=
A F'^2 r
+B n^2\frac{F^2}{r}
+\frac{C}{2}(F^2-1)^2r.
 $$ 

Here:

- \(A\) is radial-gradient stiffness;
- \(B\) is phase-gradient stiffness;
- \(C\) is depletion/compressibility stiffness;
- \(n\) is winding number.

## 3. Euler--Lagrange equation

The Euler--Lagrange equation is

$$ 
\frac{d}{dr}\frac{\partial\mathcal L_r}{\partial F'}-
\frac{\partial\mathcal L_r}{\partial F}=0.
 $$ 

Since

$$ 
\frac{\partial\mathcal L_r}{\partial F'}=2AF'r,
 $$ 

and

$$ 
\frac{\partial\mathcal L_r}{\partial F}=2Bn^2\frac{F}{r}+2CF(F^2-1)r,
 $$ 

one obtains

$$ 
A(rF''+F')-Bn^2\frac{F}{r}-CF(F^2-1)r=0.
 $$ 

After division by \(Ar\),

$$ 
F''+\frac{F'}{r}
-\frac{B}{A}n^2\frac{F}{r^2}
-\frac{C}{A}F(F^2-1)=0.
 $$ 

Equivalently,

$$ 
\boxed{
F''+\frac{F'}{r}
-\frac{B}{A}n^2\frac{F}{r^2}
+\frac{C}{A}F(1-F^2)=0.
}
 $$ 

The canonical GP/NLSE vortex equation used in v10B.1 is recovered if

$$ 
\boxed{A=B=C,
\qquad n=1.}
 $$ 

## 4. Why the factor 1/2 is required

If the nonlinear ODE term is

$$ 
\lambda_{\rm ODE}F(1-F^2),
 $$ 

then the depletion energy must contain

$$ 
\lambda_{\rm energy}(F^2-1)^2r,
\qquad
\lambda_{\rm energy}=\frac12\lambda_{\rm ODE}.
 $$ 

Therefore for \(\lambda_{\rm ODE}=1\), the correct depletion-energy coefficient is

$$ 
\boxed{\lambda_{\rm energy}=\frac12.}
 $$ 

The v10B.0 coefficient \(1/4\) corresponds to \(\lambda_{\rm ODE}=1/2\), not to the ODE that was actually solved.

## 5. Canon implication

v11B.0 does not yet prove \(A=B=C\) from deeper SST axioms. It proves the conditional theorem:

$$ 
\boxed{
A=B=C,
\ n=1
\quad\Longrightarrow\quad
\text{canonical GP/NLSE core equation and }\alpha_{\rm ring}^{\rm GP}\approx1.61935.
}
 $$ 

To upgrade to locked CANON, SST must supply an internal lemma that fixes the equality of radial-gradient, phase-gradient, and depletion stiffnesses.