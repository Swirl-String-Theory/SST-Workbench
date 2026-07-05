# SST chi-phase package v14B.0

**Track:** B — internal `A=B=C` gate for the GP/NLSE core-envelope reduction.  
**Status:** derived-conditional theorem / proposed CANON gate.

This package answers the remaining question after v11B.0--v13B.0:

> When may the GP/NLSE coefficients be treated as internally derived from SST rather than imported as an external effective model?

The answer is precise:

$$
A_{\rm grad}=B_{\rm phase}=C_{\rm depletion}
$$

is internally derived if the resolved SST string core has a **single isotropic complex envelope**

$$
\Psi=F e^{i n\theta}
$$

with one stiffness modulus in the transverse core plane.

## Radial energy convention

v14B.0 uses

$$
\mathcal L_r
=
A F'^2 r
+B n^2\frac{F^2}{r}
+\frac{C}{2}(F^2-1)^2r.
$$

Variation gives

$$
F''+\frac{F'}{r}
-\frac{B}{A}n^2\frac{F}{r^2}
+\frac{C}{A}F(1-F^2)=0.
$$

Therefore the unit GP/NLSE vortex ODE used by v10B.1--v12B.0 follows for

$$
A=B=C,
\qquad n=1.
$$

The old v10B.0 factor `1/4` corresponds to `C=1/2`, not `C=1`, and is therefore inconsistent with the solved unit ODE.

## Canon status

v14B.0 does **not** claim that SST has already locked the one-modulus core-envelope axiom. It proves the conditional theorem:

$$
\boxed{
\text{single isotropic SST core envelope}
\Longrightarrow
A=B=C
\Longrightarrow
\text{unit GP/NLSE vortex ODE.}
}
$$

To upgrade the Track B result to **CANON-derived**, the canon must accept the single-isotropic-core-envelope lemma as part of the resolved-core sector.

## Run

```bash
cd sst_chi_phase_package_v14B0
python simulate_chi_phase_v14B0.py
```

Outputs are written to `exports/`.