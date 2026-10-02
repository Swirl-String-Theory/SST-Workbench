# CANON status for v11B.0

## Classification

**Strong Research Track / derived-conditional.**

v11B.0 provides the variational bridge missing from v10B.1: the GP/NLSE vortex ODE follows from a minimal SST core-envelope energy if the internal envelope stiffnesses satisfy

$$ 
A_{\rm grad}=B_{\rm phase}=C_{\rm depletion}.
 $$ 

## Canon-safe theorem

$$ 
\mathcal L_r=A F'^2r+B n^2\frac{F^2}{r}+\frac{C}{2}(F^2-1)^2r
 $$ 

implies

$$ 
F''+\frac{F'}{r}-\frac{B}{A}n^2\frac{F}{r^2}+\frac{C}{A}F(1-F^2)=0.
 $$ 

Thus the v10B.1 equation is recovered for \(A=B=C,n=1\).

## What is still missing for locked CANON

A deeper SST argument must fix \(A=B=C\) without importing the GP/NLSE convention. Candidate routes:

1. isotropic internal-envelope stiffness from the same quadratic core Hamiltonian;
2. a phase-density amplitude reduction of the existing SST torsional field;
3. a variational principle tying depletion stiffness to phase stiffness through incompressibility/finite core capacity.

## Numerical status

The default v11B.0 run reproduces the v10B.1 positive Track B result:

$$ 
\alpha_{\rm ring}^{\rm GP}(\infty)\approx1.61935,
\qquad
\beta_{\rm ring}^{q=0}(\infty)\approx0.61935.
 $$ 

This is close to the legacy NLS pair \((1.61,0.61)\), but remains conditional until the stiffness-lock lemma is accepted.