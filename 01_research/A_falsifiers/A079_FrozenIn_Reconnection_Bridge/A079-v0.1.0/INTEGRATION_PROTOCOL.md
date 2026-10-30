# STTC v0.1.0 — SST Topological Transport Certificate

## Purpose and epistemic statuses

* **ORTHODOX**: Cauchy/Kelvin/Helmholtz ideal transport, helicity, regular isotopy.
* **DERIVED**: the Euler spacetime two-form and manufactured analytical tests here.
* **RESEARCH_TRACK**: whether actual SST finite-core knots interacting with fully coupled background filaments pass these diagnostics, and whether those structures generate effective gravitation.
* **CURRENT SCIENTIFIC STATUS**: `NOT_EVALUATED`. A manufactured-solution PASS is not physical SST verification.

The two 2026 GR papers concern the tetrad derivative `F^ahat=d A^ahat` and a conditional ideal Ohm-type law. Here, a **different** physical fluid two-form is defined. No assertion of equality of the two form fields, or of gravitation as fluid mechanics, follows.

## Exact fluid formulation

For an unforced, constant-density, incompressible, inviscid Euler fluid, with absolute evolution parameter `t`:

```latex
\begin{aligned}
&\partial_t\mathbf v+(\mathbf v\cdot\nabla)\mathbf v=-\nabla p/\rho_{\!f},\\
&\nabla\cdot\mathbf v=0,\quad \boldsymbol\omega=\nabla\times\mathbf v,\\
&B=p/\rho_{\!f}+|\mathbf v|^2/2,\\
&\mathcal A=v_i\,dx^i-B\,dt,\quad \mathcal F=d\mathcal A,\quad U=\partial_t+v^i\partial_i,\\
&\iota_U\mathcal F=0\ \Longrightarrow\ \mathcal L_U\mathcal F=0,\\
&\partial_t\boldsymbol\omega=\nabla\times(\mathbf v\times\boldsymbol\omega).
\end{aligned}
```

For an arbitrary differentiable field where Euler may fail, define

```latex
\mathbf r:=\partial_t\mathbf v-\mathbf v\times\boldsymbol\omega+\nabla B.\\
\partial_t\boldsymbol\omega=\nabla\times(\mathbf v\times\boldsymbol\omega)+\nabla\times\mathbf r.
```

A smooth global transport redefinition exists **if** there are globally smooth `zeta`, `chi` with `r=zeta x omega+grad chi` and `w=v+zeta` sufficiently regular, making the induction equation ideal in `w`. The existence of a nonzero residual or of nonzero `curl(r)` does not itself certify reconnection. In an actual fluid simulation, `omega` must be computed consistently as `curl(v)`; the kinematic induction-only slippage control in this pilot is intentionally not counted as an Euler solution.

For periodic or impermeable boundaries with vanishing helicity boundary flux:

```latex
H_\omega=\int_V\mathbf v\cdot\boldsymbol\omega\,d^3x,
\qquad \frac{dH_\omega}{dt}=2\int_V\mathbf r\cdot\boldsymbol\omega\,d^3x.
```

The source term has dimensions `[r . omega]=m/s^3`, `[H]=m^4/s^2`, `[dH/dt]=m^4/s^3`. A lack of helicity conservation does not on its own imply a topological reconnection (the exact viscously decaying ABC field is the negative control).

For a material tube segment whose tangent is `T0`, under a prescribed invertible volume-preserving deformation gradient `F`:

```latex
J=\det F=1,\qquad \boldsymbol\omega_t=F\boldsymbol\omega_0,\\
\lambda=|F\hat{\mathbf T}_0|,\qquad A_t=A_0/\lambda,\\
\Gamma_t=(\boldsymbol\omega_t\cdot\hat{\mathbf T}_t)A_t=\Gamma_0,\\
A_t\,ds_t=A_0\,ds_0.
```

These are kinematical Cauchy identities, not proof of a self-consistent Euler solution with the prescribed nonzero knotted vorticity. A finite-core filament must also address `core_radius`, cross-section distortion and vortex stretching, without silently keeping both all radii and length constant.

## Exact adapter boundaries

| Read-only source family | Version visible in Drive | Input supplied by family | Additional STTC qualification required | Do **not** infer |
|---|---|---|---|---|
| A016 Helmholtz transport | v0.2.2 | Cauchy P0-P2, flow/geometry H0-H4, exterior P3-P6, provider X0 | spacetime two-form residual; frozen-in as new sibling diagnostic | stable physical knotted vortex or new PASS to original gates |
| A007 ideal links | v0.4.0-alpha.1 | integer Gauss linking, topology sector identity, higher-invariant-needed flag | preserved component identity, material isotopy, optional Milnor triple in a separately qualified extension | ordinary helicity certifies Borromean link |
| A037 chirality/helicity | v0.3.3 | source-conditioned helicity proxies, parity PC02 | compare H(t) with `2 integral r.omega`, gauge and boundary flux audit | polarization/transport/antimatter from H alone |
| A047 Euler regularity | v0.4.0 inventoried, unqualified | regularity and finite-time bounds | time interval / smooth flow / nonvanishing core admission, stop on unresolved | global regularity or smooth-isotopy proof |
| A038 trefoil dynamics | v0.5.1 | PC04, finite-core native evolution and operator-split remeshing | fixed physical end time and separate dt/h/core convergence, material tracer integrity | numerical trajectory = full 3D Euler |
| E011 SKLSA | v0.3.0 STATIC_READY | selected geometries descended from E010-v0.3.1 | byte-level dataset/anchor admission and effective parent capability | time dynamics or independently qualified physics |
| E010 PKLSA | v0.4.0 combined research intake | historical and Ruban research geometry, status flags | research-only fork if non-admitted, no silent auto-promotion | Ruban 3D dynamics already certified |
| A060 evidence postrun | v0.3.0 inventory-only | sealed machine-readable inputs and source hashes | import outcomes **after** all upstream scientific prerequisites, without changing raw gates | post-run synthesis promotes analytic smoke to physical law |

The Workbench v1.0.10 migration preflight reported a current PACKAGE_MANIFEST mismatch for `docs/DD32_FP32X2.md`. **No framework canonical mutation or migration, no family release, no catalog update and no unattended runs were performed**. A source audit is a prerequisite for release engineering, separate from the mathematical content.

## Real source admission observed 29 October 2026

The original E011 static archive `E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip`, read from Drive, matches its external SHA256:

`97cd1acbf23c102e4564f2d74fd329a2d03f32a29b8bd376ffa8b806c14246cc`.

The release declares 47 provider anchors, 431 primary STATIC_READY entries and 45 topological selections. This is a **static metadata and provenance precheck**. The selected archive does **not** supply physical time-dependent finite-core trajectories. Writhe anchor comparison:

| Topology | Gilbert Wr | KnotPlot Wr | E011 full-provider abs(Wr) status |
|---|---:|---:|---|
| `3_1` | -3.4183529020 | +3.4105983794 | AGREEMENT_STRONG |
| `5_2` | +4.5456528866 | +4.6837383417 | AGREEMENT_STRONG |
| `6_1` | -1.1136936508 | +1.3724727130 | AGREEMENT_WEAK |

The positive/negative anchor Wr signs are not interpreted without orientation, component ordering and mirror conventions.

## Gates, stop criteria and release states

**ALPHA (this package):** manufactured Beltrami Euler field, finite-difference curl spatial convergence, exact viscous decay negative control, RK4 scalar temporal convergence, smooth kinematic induction slippage, Hopf Gauss linking, trefoil Cauchy tube transport, flat rotating tetrad diagnostic and real E011 static metadata admission. Each has threshold in `GATE_LEDGER.json`. **20 analytical checks PASS.** This is *not* a full computational-fluid-dynamics (CFD) knot certification.

**NEXT 1 (read-only cross-falsifier integration):** freeze family input SHA256 (admitted raw geometry and actual trajectory/velocity output), dimensions, BC, units, `rho_f`, `r_c`, circulation, numerical kernel, mesh/remap scheme, private source seals and claim-specific preregistered thresholds. Source hashes cannot be copied from the metadata archive and treated as raw-trajectory hashes. Reject any ineligible carrier or topology-identity ambiguity without synthetic substitution.

**NEXT 2 (full finite-core):** ring analytic benchmark, free trefoil, trefoil+one background line, trefoil+several fully dynamic lines, discrete lattice vs homogeneous/coarse-grained rotation with matching mean vorticity `Omega=Gamma/(2d^2)`. Separate full-field velocity residual, no-reconnection topology, tube material tracers, helicity and boundary flux. Use actual dynamic fields, not solely point-cloud visual proximity.

**NEXT 3 (certification):** same physical final time; spatial, temporal, finite-core convergence independently; no mesh-only or remeshing artifact. Exact raw link identities and clean blind/reveal where test compares anonymous sectors. Stop with `UNRESOLVED` on missing proof, `NOT_RUN` if no admitted dynamics or `FAIL` on converged contradictory observation, never guessed `PASS`.

For physical topology, a crossing in a 2D projection is not reconnection; a close 3D approach is not reconnection. Require a genuine change in 3D link/isotopy identity, verified under resolution refinements; the absence of observed reconnection during finite simulation does not prove indefinite stability.

## Citations, copy-ready LaTeX

```latex
\begin{thebibliography}{9}
\bibitem{AsenjoWinklerComisso2026}
F. A. Asenjo, M. A. Winkler and L. Comisso,
``Frozen-In Gravitational Fields,''
Phys. Rev. Lett. \textbf{136}, 161401 (2026).
\href{https://doi.org/10.1103/6c4q-kx6f}{doi:10.1103/6c4q-kx6f}.
\bibitem{ComissoAsenjo2026}
L. Comisso and F. A. Asenjo,
``Reconnection of Gravitational Fields,''
Phys. Rev. D \textbf{114}, 084095 (2026).
\href{https://doi.org/10.1103/lmqy-pf9k}{doi:10.1103/lmqy-pf9k}.
\bibitem{Newcomb1958}
W. A. Newcomb, ``Motion of Magnetic Lines of Force,''
Ann. Phys. \textbf{3}, 347--385 (1958).
\href{https://doi.org/10.1016/0003-4916(58)90024-1}{doi:10.1016/0003-4916(58)90024-1}.
\bibitem{Moffatt1969}
H. K. Moffatt, ``The Degree of Knottedness of Tangled Vortex Lines,''
J. Fluid Mech. \textbf{35}, 117--129 (1969).
\href{https://doi.org/10.1017/S0022112069000991}{doi:10.1017/S0022112069000991}.
\end{thebibliography}
```
