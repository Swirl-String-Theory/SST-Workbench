# v13B.0 derivation note — unified Track A/B benchmark

## 1. Ring-constant definitions

The vortex-ring Hamiltonian is written as

$$ 
E(R,a)=\frac12\rho\Gamma^2R
\left[\ln\left(\frac{8R}{a}\right)-\alpha_{\rm ring}\right].
 $$ 

The ring speed convention is

$$ 
U=\frac{\Gamma}{4\pi R}
\left[\ln\left(\frac{8R}{a}\right)-\beta_{\rm ring}\right].
 $$ 

For a core-growth law

$$ 
q=\frac{d\ln a}{d\ln R},
 $$ 

Hamiltonian differentiation \(U=dE/dP\), with \(P=\rho\Gamma\pi R^2\), gives

$$ 
\beta_{\rm ring}=\alpha_{\rm ring}-1+q.
 $$ 

This relation is robust. It does not fix the absolute value of \(\alpha_{\rm ring}\).

## 2. Track A

Track A computes the incompressible Euler/Biot--Savart vorticity energy

$$ 
E_{\rm BS}=\frac{\rho}{8\pi}\int\!\int
\frac{\boldsymbol\omega(\mathbf x)\cdot\boldsymbol\omega(\mathbf x')}
{|\mathbf x-\mathbf x'|}\,d^3x\,d^3x'.
 $$ 

The extracted intercept is

$$ 
\alpha_{\rm eff}=\ln\left(\frac{8R}{a}\right)-\frac{2E_{\rm BS}}{\rho\Gamma^2R}.
 $$ 

Track A is canon-compatible because it stays within incompressible vortex mechanics. Its key result is negative for the NLS target: smooth matched profiles near the \(\chi\)-closure root give \(\alpha_{\rm ring}\approx1.50\), not \(1.61\).

## 3. Track B

Track B uses the unit-winding GP/NLSE core-envelope ODE

$$ 
F''+\frac{F'}{r}-\frac{F}{r^2}+F(1-F^2)=0.
 $$ 

The energy integrand consistent with this ODE is

$$ 
I(r)=\frac{F^2}{r}+(F')^2r+\frac12(F^2-1)^2r.
 $$ 

The log-subtracted core constant is

$$ 
C(R)=\int_0^R I(r)\,dr-\ln R,
 $$ 

and in the convention used by v10B.1--v12B.0,

$$ 
\alpha_{\rm ring}^{\rm GP}=2-C_\infty.
 $$ 

The large-\(r\) tail is algebraic:

$$ 
F(r)=1-\frac{1}{2r^2}-\frac{9}{8r^4}-\frac{161}{16r^6}+\cdots,
 $$ 

which implies

$$ 
C_\infty-C(R)=-\frac{1}{4R^2}+\frac{1}{4R^4}+\frac{11}{6R^6}+\cdots.
 $$ 

This justifies the asymptotic extraction used in v12B.0.

## 4. Unified conclusion

Track A and Track B are not redundant.

$$ 
\alpha_{\rm ring}^{A}[\text{smooth }a_0^\star]\approx1.504718,
 $$ 

while

$$ 
\alpha_{\rm ring}^{B}[\text{GP/NLSE},\infty]\approx1.619350923.
 $$ 

Therefore the \(\chi\)-closure selector and the GP/NLSE ring-energy selector are distinct.

This does not weaken Track B. It sharpens the epistemology: the old NLS value near \(1.61\) is not a generic incompressible Euler result; it requires the GP/NLSE gradient and density-depletion core energy.