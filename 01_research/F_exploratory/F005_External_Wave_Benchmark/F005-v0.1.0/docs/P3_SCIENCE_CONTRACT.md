# F005 v0.5.0-p3 — Frozen science contract (DEVELOPMENT)

## Inheritance and provenance

- Original F005 instance root, v0.4.3 `proxy_family_development_split.csv` SHA-256 `d60bfe0daa8195290958ca0b8f6268e01bf93811267e6c80b02cfadaa84d37a2`.
- v0.4.3 descriptive validation metrics SHA-256 `024af63a4319a5159b40fb11ed33d83afb72195a5ac43647f8c060efd4b27af5`.
- Robot `INPUT_TRAIN.npy` SHA-256 `5d51b77ecf20cc4327c11a416e5e70c42a63c8499b8f9ba7c0af1fdc35af3aed`.
- Camilotto geometry JSON SHA-256 `91f6c876a1ae215dc5bce6c70ce6f192aeb667b9c4e2397d102c53271dca0793`.
- p2 report must still block `E0_MAIN_EULER_GATE`, provenance signs and pre-motion evidence. The p2 report is read but not changed.
- Predesignated 850 `DEV_VALIDATION` members are the ONLY `OUTPUT_TRAIN.npy` responses indexed. The other 8,972 rows remain unopened by the p3 normal run. Note: the original TRAIN+VALIDATION development pool has been inspected in prior releases; it is NOT blind.

## Physics (source-geometry-only)

$$\nabla^2\phi=0,\qquad k_n=\frac{(2n+1)\pi}{L},\qquad \omega_n^2=(gk_n+\sigma k_n^3/\rho)\tanh(k_nh).$$

$$\ddot q_n + \omega_n^2 q_n = - k_n\tanh(k_nh) b_n a(t),\quad b_n=\frac{4(-1)^n}{Lk_n^2},\quad \eta(x,t)=\sum_{n=0}^3q_n(t)\sin(k_nx).$$

L=0.080 m, B=0.031 m, h=0.043 m, x=+0.040 m, model rho=998 kg/m³, g=9.81 m/s², sigma=0 by *model assumption*. The solver is the exact piecewise-constant forcing recurrence from frozen v0.5.0. This is not general nonlinear Euler fluid dynamics, a 3D bulk-flow solution, Kelvin wave propagation, or PKLSA.

## Modal-state identifiability

At fixed anchor `t0`, two observed heights `eta[t0-dt],eta[t0]` impose exactly two linear scalar conditions on 8 unknown modal state variables. The first-order inverse ZOH relation is used to seed the 4-mode minimum state while leaving 6 unknowns set to zero; the `E4_SENSITIVITY` cases change these six unknowns and re-solve the fundamental mode so both observations stay the same.

Each perturbation is performed in exactly one of high modes n=1,2,3 as either modal *wall contribution* `±0.25 mm` in initial elevation or `±5 mm/s` in initial derivative. Including the minimum seed there are 13 cases, fixed independently of validation signals. They are not probability distributions, measured bounds or calibrated nuisance parameters.

## Evaluation rules

1. No response teacher forcing after anchor. The known future accelerations are supplied unchanged. The assumed-rest model starts at t=0 with zero amplitude and velocity and receives no measured height at all.
2. The `from_rest` result is scored separately from conditional models. Historic v0.4.3 baselines have two observed anchor height seeds, so their comparison with a from-rest run is **not like-for-like**.
3. `conditional` one-mode and 4-mode minimum-seed results may be displayed with previously frozen ARX/oscillator aggregate scores for the same 850 development trajectories, fixed 3 anchors and 5 horizons. No statistical independence claim or aggregate superiority claim is authorized.
4. Report full-trajectory RMSE and endpoint RMSE in millimetres; preserve results for each anchor/horizon, no cherry picking.
5. `E9` height/depth >0.2 is a *review heuristic*, not a derived strict linearization threshold; absence of trigger does not prove small slopes.
6. Every result is development. Do not promote E0, P7/PKLSA, E8/SST physical claims or family independence.

## Falsifiers and limitations

A suitable physical model must predict a phase-consistent response for individually documented initial states and coordinate signs, without using validation data for nuisance parameter selection. A large sensitivity envelope falsifies **state identifiability from two scalar height samples**, not Euler dynamics. Apparatus-level mismatches can arise from dissipation, meniscus, transverse flow and nonlinearity; they are not SST evidence.

## References

```latex
\begin{thebibliography}{9}
\bibitem{Camilotto2026} D. Camilotto (2026),
``A Comprehensive Data-Driven Framework for Robotic Liquid Sloshing Control:
From Extensive Experimental Model Validation and Enhancement to Trajectory Optimization,''
Master's thesis, Politecnico di Milano,
\url{https://hdl.handle.net/10589/253216}.
\bibitem{FaltinsenTimokha2009} O. M. Faltinsen and A. N. Timokha (2009),
\emph{Sloshing}, Cambridge University Press, ISBN 9780521881111.
\bibitem{Giulietti2026} N. Giulietti, M. Bedodi, D. Ghavami, D. Camilotto, H. Giberti (2026),
``Robot-executed longitudinal sloshing dataset for rectangular tank liquid handling,''
Zenodo v1.0.0, \url{https://doi.org/10.5281/zenodo.20039757}.
\end{thebibliography}
```
