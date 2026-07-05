# SST chi-phase package v11B.0

**Track B:** SST core-envelope → GP/NLSE vortex ODE reduction audit.

This package continues v10B.1 using the new versioning scheme:

- **v11B.0** — derive/check the GP/NLSE core equation from an SST core-envelope energy.
- **v12B.0** — asymptotic tail proof and numerical validation.
- **v13B.0** — unified Track A/Track B alpha-ring benchmark pipeline.

## Why v11B.0 exists

v10B.1 corrected the GP/NLSE depletion-energy coefficient and found

$$ 
\alpha_{\rm ring}^{\rm GP}(\infty)\approx1.61935,
\qquad
\beta_{\rm ring}^{q=0}(\infty)\approx0.61935.
 $$ 

That is close to the legacy NLS pair \((1.61,0.61)\), but v10B.1 is still an effective-core result unless the GP/NLSE vortex equation is derived from SST's internal core-envelope assumptions.

v11B.0 supplies the variational bridge:

$$ 
\mathcal L_r
=
A F'^2 r
+B n^2\frac{F^2}{r}
+\frac{C}{2}(F^2-1)^2r.
 $$ 

Euler--Lagrange gives

$$ 
F''+\frac{F'}{r}
-\frac{B}{A}n^2\frac{F}{r^2}
+\frac{C}{A}F(1-F^2)=0.
 $$ 

The v10B.1 GP equation follows when

$$ 
A=B=C,
\qquad n=1.
 $$ 

So the corrected energy coefficient \(1/2\) is not a fit. It is forced by variational consistency.

## Canon status

Current status:

$$ 
\boxed{\text{Strong Research Track / derived-conditional.}}
 $$ 

It becomes **CANON-derived** only if SST canonically fixes the three envelope stiffnesses:

$$ 
A_{\rm grad}=B_{\rm phase}=C_{\rm depletion}.
 $$ 

Until then, the result should be phrased as:

> Assuming the SST core-envelope reduces to the canonical GP/NLSE functional with equal gradient, phase, and depletion stiffnesses, the ring constant is derived as \(\alpha_{\rm ring}^{\rm GP}\approx1.61935\).

## Run

```bash
python simulate_chi_phase_v11B0.py
```

Optional:

```bash
python simulate_chi_phase_v11B0.py --r-right 100 --r-eval 15.5 --tol 1e-9
```

## Exports

The script writes:

- `exports/chi_v11B0_euler_lagrange_reduction.csv`
- `exports/chi_v11B0_energy_consistency.csv`
- `exports/chi_v11B0_coefficient_scan.csv`
- `exports/chi_v11B0_core_constants.csv`
- `exports/chi_v11B0_convergence.csv`
- `exports/chi_v11B0_asymptotic_fit.csv`
- `exports/chi_v11B0_residual.csv`
- `exports/chi_v11B0_results.json`
- `exports/chi_v11B0_convergence.png`
- `exports/chi_v11B0_run_results_summary.txt`