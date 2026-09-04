# S37C remap-kernel audit — v0.3.3

## Finding

The v0.3.2 preregistered numerical intent was a **periodic-cubic arclength remap** separated from the physical RK4 operator.  The released implementation instead called the legacy `geometry.resample_closed`, whose coordinate interpolation is `numpy.interp`, i.e. piecewise linear interpolation on the current polygon.

This matters because repeated polygonal remapping is not a pure relabeling of a smooth embedded centerline at finite resolution: it repeatedly replaces the discrete representation and can feed interpolation error into the subsequently evaluated Biot--Savart field.

The KAtlas v0.3.2 smoke therefore remains a valid negative diagnostic for that *implemented* map, but it is not a clean test of the preregistered periodic-cubic S37C map.

## Corrective map

v0.3.3 defines

\[
\mathbf X^-_{n+1}=\Phi_{\Delta t}^{\mathrm{RK4}}[\mathbf X_n],
\qquad
\mathbf X_{n+1}=\mathcal R^{(3)}_s[\mathbf X^-_{n+1}],
\]

where \(\mathcal R^{(3)}_s\) is constructed as follows:

1. cumulative chord length supplies the periodic spline knot parameter;
2. a periodic cubic spline \(\mathbf S(u)\) is fitted through all markers;
3. spline arclength is estimated on a dense, fixed-rule quadrature grid;
4. that arclength map is inverted to equal-arclength target locations;
5. the first marker is restored exactly as the cyclic phase anchor.

No tangential velocity enters any RK4 stage.

## Gate policy

No S37C physics threshold is loosened.  The gate still requires, at minimum,

\[
D_{\max}^{\rm cadence}(N_{\max})\le D_{\rm gate},
\qquad
p=-\frac{d\ln D_{\max}^{\rm cadence}}{d\ln N}\ge p_{\min},
\]

plus the frozen score-span and AUC-span gates.  The legacy linear remapper is retained only as an explicit diagnostic kernel and cannot silently become the primary map.

A pass certifies only numerical closure of the regularized filament surrogate under this reparameterization family.  It does **not** establish full 3-D Euler stability or SST.
