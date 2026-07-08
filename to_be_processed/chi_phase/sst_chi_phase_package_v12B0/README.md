# SST chi-phase package v12B.0

**Track:** B — GP/NLSE algebraic-tail and asymptotic `alpha_ring` extraction audit  
**Status:** Strong Research Track / asymptotic-extraction support; not locked CANON

## Purpose

v10B.1 corrected the GP/NLSE energy coefficient and found

$$ 
\alpha_{\rm ring}^{\rm GP}\approx 1.619,
\qquad
\beta_{\rm ring}^{q=0}\approx 0.619.
 $$ 

v11B.0 showed that the solved GP/NLSE vortex ODE follows from a canonical radial core-envelope functional if the SST stiffnesses are locked as \(A=B=C\).

v12B.0 tests the next gate: the algebraic far-field tail used to extrapolate finite-radius core constants to \(R\to\infty\). This package makes the extrapolation law non-ad hoc.

## Canonical GP/NLSE vortex ODE

The package solves

$$ 
F''+\frac{F'}{r}-\frac{F}{r^2}+F(1-F^2)=0,
\qquad
F(0)=0,
\qquad
F(\infty)=1.
 $$ 

The corrected GP/NLSE radial energy integrand is

$$ 
I(r)=\frac{F^2}{r}+(F')^2r+\frac12(F^2-1)^2r.
 $$ 

The log-subtracted core constant is

$$ 
C(R)=\int_0^R I(r)\,dr-\ln R,
\qquad
\alpha_{\rm ring}(R)=2-C(R).
 $$ 

## Analytic far-field result

Substitution of

$$ 
F(r)=1+\sum_{k\ge1}a_k r^{-2k}
 $$ 

into the vortex ODE gives

$$ 
F(r)=1-\frac{1}{2r^2}-\frac{9}{8r^4}-\frac{161}{16r^6}-\frac{24661}{128r^8}+\cdots .
 $$ 

Then

$$ 
I(r)-\frac1r
=
-\frac{1}{2r^3}+\frac1{r^5}+\frac{11}{r^7}+\frac{179}{r^9}+\cdots .
 $$ 

Therefore

$$ 
C_\infty-C(R)
=
\int_R^\infty \left(I(r)-\frac1r\right)dr
=
-\frac{1}{4R^2}+\frac{1}{4R^4}+\frac{11}{6R^6}+\frac{179}{8R^8}+\cdots .
 $$ 

Equivalently,

$$ 
C(R)
=
C_\infty
+\frac{1}{4R^2}
-\frac{1}{4R^4}
-\frac{11}{6R^6}
-\frac{179}{8R^8}
+\cdots .
 $$ 

This is why v10B.1/v11B.0 used a \(1/R^2+1/R^4\) extraction law. v12B.0 validates it analytically and numerically.

## Run

```bash
python simulate_chi_phase_v12B0.py
```

Optional:

```bash
python simulate_chi_phase_v12B0.py --r-right 200 --tol 1e-9
```

## Outputs

The script writes to `exports/`:

- `chi_v12B0_tail_coefficients.csv`
- `chi_v12B0_expected_C_fit_coefficients.csv`
- `chi_v12B0_convergence.csv`
- `chi_v12B0_F_tail_validation.csv`
- `chi_v12B0_unconstrained_fits.csv`
- `chi_v12B0_analytic_tail_stats.csv`
- `chi_v12B0_jackknife.csv`
- `chi_v12B0_principal_estimate.csv`
- `chi_v12B0_results.json`
- `chi_v12B0_run_results_summary.txt`
- `chi_v12B0_tail_corrected_alpha.png`
- `chi_v12B0_F_tail_error.png`

## Interpretation

v12B.0 does not yet lock the result as CANON. It supports the following conditional theorem:

$$ 
\boxed{
\text{If the SST core-envelope is GP/NLSE locked with }A=B=C,
\text{ then the asymptotic extraction of }\alpha_{\rm ring}^{\rm GP}
\text{ is algebraically justified.}
}
 $$ 

The remaining locked-CANON gate is still the SST-internal derivation of \(A=B=C\).