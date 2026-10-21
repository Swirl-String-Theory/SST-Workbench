# F005 v0.5.0 SCIENCE CONTRACT - FROZEN DEFINITION

## Scope

**Independent linearized potential-Euler multimodal baseline**, a mathematically derived limiting regime of the inviscid Euler equations, not nonlinear Euler CFD, not Kelvin/inertial vortical modes, and not PKLSA. It must not reuse ARX/oscillator frequencies, damping or gain. Strong candidate SST physics statements remain UNRESOLVED.

## Domain and governing equations

For a rigid rectangular container translating along a measured longitudinal x-axis, choose the tank's *wet internal* length `L`, width `B`, static fill depth `h`, x in `[-L/2,L/2]`, and z in `[-h,0]`, with gravity `g` and surface-tension `sigma`. Assume 2D spanwise-uniform, inviscid, incompressible, irrotational small-amplitude motion. The velocity potential satisfies

```latex
\nabla^2\phi=0,\quad \partial_x\phi\big\vert_{x=\pm L/2}=0,\quad
\partial_z\phi\big\vert_{z=-h}=0,
\quad \partial_t\eta=\partial_z\phi\big\vert_{z=0},
\quad \partial_t\phi+g\eta-\frac{\sigma}{\rho}\partial_{xx}\eta=-a(t)x
\quad(z=0).
```

This yields the odd longitudinal Neumann modes (tank-fixed frame)

```latex
k_n=\frac{(2n+1)\pi}{L},\qquad
\omega_n^2=\left(gk_n+\frac{\sigma}{\rho}k_n^3\right)\tanh(k_nh),
\qquad n=0,1,\dots,N-1,
```

with `x=0` at the centre and no lateral wall mode because spanwise invariance is assumed. Expanding `x` into sine modes:

```latex
x=\sum_{n=0}^{\infty}b_n\sin(k_nx),\qquad
b_n=\frac{4(-1)^n}{L k_n^2}.
```

The amplitude equations (SI) are

```latex
\ddot q_n(t)+\omega_n^2q_n(t)
=-k_n\tanh(k_nh)b_n a(t),\qquad
\eta(x,t)=\sum_{n=0}^{N-1}q_n(t)\sin(k_nx).
```

Here `q_n` and `eta` are metres, `omega_n` rad/s, acceleration m/s^2; the forcing coefficient is dimensionless. Exact ZOH forcing for each sampling interval `dt` is used:

```latex
q_{j+1}=c q_j+\frac{s}{\omega}v_j+\frac{1-c}{\omega^2}F_j,\qquad
v_{j+1}=-\omega s q_j+c v_j+\frac{s}{\omega}F_j,\quad
c=\cos(\omega\Delta t),\ s=\sin(\omega\Delta t).
```

For `a(t)=a0` constant, `q_n(t)=F_n(1-cos(omega_n t))/omega_n^2` from rest. For `sigma=0` and small acceleration, the equilibrium wall elevation approaches `-aL/(2g)` as N increases; this is tested. For `kh<<1`, `omega²≈g h k²` (gravity-only). For `kh>>1`, `omega²≈g k`.

## Required source inputs

1. True *internal wetted* longitudinal length and water depth; T75 nominal outer size is insufficient.
2. Actual sensor coordinate `x`, its height polarity and forcing acceleration polarity. The dataset only identifies a longitudinal wall measurement in public metadata.
3. Water properties, temperature as available, known gravity, and reason the vessel can be treated as 2D rectangular.
4. Evidence that each trajectory begins from near-equilibrium if primary from-rest forecasts are to be considered physically interpretable.
5. Text/DOI/measurement provenance of geometry. Never infer it from ARX ~2.87 Hz or independently fitted oscillator ~2.94 Hz.

If any required field absent, `E0=BLOCKED`. No measured validation signal is read and no physical metric is produced. The example DEMO is not an experimental measurement.

## Immutable data and selection

- `EXPECTED_SPLIT_SHA256 = d60bfe0daa8195290958ca0b8f6268e01bf93811267e6c80b02cfadaa84d37a2` (v0.4.3 CSV)
- `EXPECTED_INPUT_SHA256 = 5d51b77ecf20cc4327c11a416e5e70c42a63c8499b8f9ba7c0af1fdc35af3aed` (Zenodo acceleration NPY)
- Only the 850 `DEV_VALIDATION` rows of the **old exposed DEVELOPMENT population** may be read from `OUTPUT_TRAIN.npy` for scoring. All original STANDARD_TEST/OPTIMIZED_OOD outputs are kept unopened/unindexed.
- Fixed anchors: `0.004,1.5,2.8 s`; horizons `0.1,0.5,1,2,3 s`; sampling `dt=0.004 s`; max 17 modes in real run.
- Start-from-rest modal initial conditions in the primary model. A secondary *single-mode* conditional comparison uses only the two initial measured wall heights at the anchor, and then freely propagates with known forcing.
- Physically different initialization policies cannot be pooled into a single win/loss metric.

## Interpretation and gates

- **E0:** geometry, sensor, forcing, initial equilibrium source-provenance and dimensional validity.
- **E1:** independent analytic modal coefficients and exact time propagator regression.
- **E2:** integrity locks on the original acceleration array and proxy-disjoint development split.
- **E3:** full-from-rest forecast on exposed development validation rows. Nonblind, with explicit starting-equilibrium assumption.
- **E4:** one-mode conditional diagnostic, not general multimodal state initialization.
- **E5:** numerical comparison to separately fitted reduced-order models only with clearly stated different initialization; no unfair superiority claim.
- **E6:** proxy family-disjoint development split. Source-defined waveform family independence unresolved.
- **E7:** source-native PKLSA not run.
- **E8:** physical SST validation unresolved.
- **E9:** `max|eta|/h` amplitude diagnostic; >0.2 triggers a large-amplitude review; lower values do not by themselves prove linearity or small slope.

Independent Euler frequencies rely only on source geometry; viscosity can produce damping experimentally and is absent from this baseline. Failure against damped experimental ringdown can falsify the adequacy of *ideal inviscid linear Euler for that apparatus* without establishing or falsifying SST's gravity/quantum hypotheses.

## Sources - LaTeX

```latex
\begin{thebibliography}{9}
\bibitem{FaltinsenTimokha2009}
O.~M. Faltinsen and A.~N. Timokha (2009),
\emph{Sloshing}, Cambridge University Press,
ISBN 978-0-521-88111-1,
\url{https://www.cambridge.org/9780521881111}.

\bibitem{FaltinsenEtAl2000}
O.~M. Faltinsen, O.~F. Rognebakke, I.~A. Lukovsky,
and A.~N. Timokha (2000),
``Multidimensional modal analysis of nonlinear sloshing in a
rectangular tank with finite water depth,''
\emph{Journal of Fluid Mechanics} \textbf{407}, 201--234,
\url{https://doi.org/10.1017/S0022112099007569}.

\bibitem{GiuliettiZenodo2026}
N. Giulietti, M. Bedodi, D. Ghavami, D. Camilotto,
and H. Giberti (2026),
``Robot-executed longitudinal sloshing dataset for rectangular
tank liquid handling,'' Zenodo v1.0.0,
\url{https://doi.org/10.5281/zenodo.20039757}.

\bibitem{Camilotto2026}
D. Camilotto (2026),
``A comprehensive data-driven framework for robotic liquid sloshing control:
from extensive experimental model validation and enhancement to trajectory optimization,''
Master's thesis, Politecnico di Milano,
\url{https://hdl.handle.net/10589/253216}.
\end{thebibliography}
```
