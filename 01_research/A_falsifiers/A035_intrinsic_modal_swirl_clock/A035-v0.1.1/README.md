# SST Intrinsic Modal Swirl-Clock Blind Falsifier v0.1.1

## Central question

> Does a relaxed finite-core vortex knot contain an **intrinsic recurrent normal mode** whose later restoring acceleration is predictively coupled to material vortex stretching, with a **measured delay** and a material-core-specific effect?

This is the post-QHP route. Q/H/P coordinates are **not used**.

## Default seed source

`..\..\KnotPlot\knots\final`

The primary campaign deliberately starts from the existing KnotPlot/Ridgerunner-relaxed centerlines. New KnotPlot seeds are not required for discovery.

## Method

Each carrier is uniformly resampled and normalized once. A small deterministic **broadband normal probe** excites several low arclength harmonics without selecting a Q/H/P mode. Matched anonymous `+/-` probe arms isolate the odd/linear response.

For the material branch:

\[
a_j^2(t)\ell_j(t)=a_{j0}^2\ell_{j0},
\]

while the null branch has fixed core radius.

Rigid translation, rigid rotation and tangential/reparameterization motion are removed before modal extraction. The odd normal response is

\[
\delta X_\perp^{(-)}(s,t)=\frac{X_+(s,t)-X_-(s,t)}{2\epsilon}.
\]

The first 40% of the trajectory is **discovery only**. POD/SVD learns spatial modes

\[
\delta X_\perp(s,t)=\sum_k a_k(t)\phi_k(s).
\]

Those `phi_k` are frozen. The remaining 60% is an independent holdout used for recurrence and causal gates. The fixed-core branch is projected onto the same material-discovered frozen basis.

## Gates

- **SC1 intrinsic mode:** non-negligible discovery energy and holdout amplitude.
- **SC2 recurrence:** >= required cycles, concentrated spectrum, harmonic holdout fit, phase-space recurrence closure and bounded amplitude.
- **SC3 stretch coupling:** project segment stretch rate onto the mode's segment-strain sensitivity and require a holdout correlation with later modal acceleration that beats phase-scramble nulls.
- **SC4 measured delay:** delay is selected only in discovery, then frozen; holdout must retain the delayed advantage over zero lag. There is no user-supplied feedback delay.
- **SC5 core specificity:** material-core candidate must outperform or survive while the fixed-core null does not.

A v0.1 `PASS_CANDIDATE_INTRINSIC_SWIRL_CLOCK` is a numerical candidate in the regularized filament/material-core model, **not** a proof of a physical clock or full 3-D Euler mechanism.


## v0.1.1 long-horizon policy

The BASIC/EXTENDED horizons are deliberately much longer than v0.1.0 so recurrence is tested over multiple periods rather than inferred from a fraction of a cycle:

| campaign | `T_final` | discovery | holdout | minimum holdout cycles |
|---|---:|---:|---:|---:|
| BASIC | 12 | 4.8 | 7.2 | 2 |
| EXTENDED | 24 | 9.6 | 14.4 | 4 |
| focus trio | 18 | 7.2 | 10.8 | 3 |
| resolution N64/96/128 | 18 | 7.2 | 10.8 | 3 |

For a tentative period near `T_mode ~ 2.9`, EXTENDED therefore contains about five holdout cycles. A clock candidate must remain coherent across those repeated cycles.

Longer time is useful only while the integration remains numerically resolved. `gate_max_ds_cv` is unchanged. The integrator also refuses to exceed `max_steps`: it will **fail loudly** rather than silently increase `dt` and violate `dt ~ ds^2`.

This release intentionally does **not** add a common-mode observable or new clock physics. It keeps the v0.1.0 odd/linear-response experiment fixed and changes the observation duration, allowing a clean test of the short-window explanation.

## Runs

```bat
run_all.cmd
run_all_extended.cmd
run_resolution.cmd
```

Explicit dataset path is optional:

```bat
run_all.cmd C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

Focused diagnostic campaigns:

```bat
run_focus_6p3.cmd
run_focus_link_4p2p1.cmd
run_focus_link_9p2p20.cmd
```

Inspect the blind result first:

`outputs\basic\analysis\blind_summary.json`

Then reveal identities:

```bat
run_reveal.cmd outputs\basic
```

## Important interpretation

Biot-Savart velocity is nonlocal. `delay` here means a **measured modal/stretch response lag**, not a finite-speed relativistic signal-propagation time.

The QHP campaign already showed that `knot_6.3` has very weak projection onto the hand-chosen Q/H/P subspace. This package therefore lets the simulated dynamics select its own spatial coordinates.

## Numerical model limits

This remains a regularized centerline Biot-Savart model with a material-core closure. It is not yet a volumetric vorticity solver and does not include a separate pressure-Poisson solve. Positive findings must later survive that stronger model.

## Resolution policy

The spatial ladder uses `N = 64, 96, 128` with the same `t_final` and the same dimensionless `dt_factor`. Since the integrator sets `dt = dt_factor * ds_min^2 / |Gamma|`, this enforces `dt ~ ds^2` without double-scaling the timestep. The resolution campaign is restricted to the three high-information carriers (`knot_6.3`, `link_4.2.1`, `link_9.2.20`) and requires the **same anonymous carrier** to remain a candidate at all three resolutions, with period spread <=20% and measured-delay spread <=25%.

## References

```latex
\begin{thebibliography}{99}
\bibitem{Saffman1992} P.~G.~Saffman, \emph{Vortex Dynamics}, Cambridge University Press (1992).
\bibitem{Holmes2012} P.~Holmes, J.~L.~Lumley, G.~Berkooz, and C.~W.~Rowley, \emph{Turbulence, Coherent Structures, Dynamical Systems and Symmetry}, 2nd ed., Cambridge University Press (2012).
\end{thebibliography}
```
