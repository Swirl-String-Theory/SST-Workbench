# Trefoil Maximum Transferable Force — distributed finite-width Euler follow-up v0.2.0

**DEVELOPMENT / NOT FROZEN / NOT CERTIFIED / NO FORCE CEILING.** This is an upgrade of v0.1.0, not a replacement. The project catalog number is deliberately **unassigned**; `family_hierarchy.json` and `catalog_index.json` need an authoritative local check. Shared **SST Falsifier Framework v1.0.10** (CANONICAL_FROZEN) is pinned in the original framework bootstrap; not bundled. No framework `FREEZE`, `BASIC`, `FULL` or `CERTIFY` was executed here.

## Scientific scope

The genuinely 3D fluid state evolves by incompressible inviscid Euler, **not** Rosenhead/Biot-Savart moving-line closure:

```
d_t u + (u · grad)u = -(1/rho)grad(p) + f;   div(u)=0
omega=curl(u),     d_t u=P[u cross omega + f]
Laplace(p) = -rho*(partial_i u_j)*(partial_j u_i) + rho*div(f)
```

Initial vorticity comes from the authenticated **Brian Gilbert ideal.txt AB 3:1:1** centerline (all coefficients in `seeds/trefoil_ideal_3_1_1.json`) by depositing a finite-support C2 kernel around the tangent integral, then projecting the gridded vorticity onto divergence-free modes. Grid projection makes support noncompact. Density, circulation and length scales are **model-normalization parameters**, NOT canon constants; e.g. rho=1 kg/m3, Gamma=1 m2/s, box 6 m, support radius a=0.22/0.26/0.28 m. Gaussian is **not** used; kernel proportional to `(1-r²/a²)^3` inside radius `a`. Time integration is fourth-order Runge--Kutta (RK4) with a two-thirds-dealiased Fourier-Galerkin velocity field. Reconstructed pressure is checked against the pressure-Poisson source. This remains a Fourier-Galerkin truncation, not continuum certification.

## Explicitly separate full-fluid shear load from actual transfer force

The applied acceleration is `f_x=A sin(2πz/B)`. Half-box net external force is `F_half=rho*A*B³/π`, opposite in the two halves. The x-momentum shear flux across z=0 is measured separately. **The load acts on the entire fluid, not directly upon a material knot clamp.** No `F_max` or breaking threshold is computed. A forced energy increase is external work input, not violation of Euler's energy law.

## Observations from the completed reduced pilot

- Nine fixed core/axial cases: best relative-equilibrium normal residual **0.212820**, with acceptance threshold **0.05**. No relative equilibrium found in that limited search.
- Independent exploratory 330-evaluation shape search, discovered on N32: residual **0.229396**. Held-out grids gave N48 **0.207647**, N64 **0.213642**; still fail 0.05. The search is bounded and does not prove absence of all Euler trefoil equilibria.
- Reduced loaded Euler pilot: N=32,48,64, fixed T=0.10 s, time step 0.0125 s, shear amplitudes A=[0,0.1,1.6] m/s², **9 completed trajectories**.
- Max relative pressure-Poisson residual **3.252e-16**, velocity divergence relative **5.900e-17** (spectral projection consistency, not continuum accuracy).
- Max unforced relative kinetic energy drift **2.980e-09** over T=0.10 s.
- Unforced N48→N64 relative energy difference **0.3386%**, material-marker length difference **0.1953%**; this is **not** sufficient to certify convergence.
- N48 independent signed geometric perturbation modes `z2`, `x3`: maximum amplification **0.999074** over 0.10 s. This shows no short-time growth in those modes at that grid, not nonlinear stability or Floquet stability.
- N64 independent perturbation run was **NOT EXECUTED** (resource limit), and the longer T=0.4 s full run was **NOT COMPLETED**. Both must remain unqualified.
- N48 core support width only 2.24 cells and N64 ~2.99 cells; finite-core resolution remains marginal and global material-marker topology is **not independently certified**.

## Executing on Windows

From the unzipped folder, in Python 3.10+ with NumPy and pytest:

```bat
python -m pip install -r requirements.txt
run_tests.cmd
run_equilibrium_search.cmd --trials 150
run_euler_pilot.cmd
```

The long physical-time diagnostic branch (significantly more costly):

```bat
run_euler.cmd --extended
```

These direct scientific scripts are distinct from the shared frozen framework. For genuine v1.0.10 instance enforcement, first inspect local catalog IDs, finish the source/holdout/protocol contracts, place or retain `private/` outside distributed BLIND, then use the unmodified `run_all.cmd FREEZE`, `BASIC`, `FULL`, `CERTIFY` as applicable. **Do not freeze this exploratory release without a new preregistration and a qualified knot-specific force measurement.** The frozen framework's general C++/Intel GPU parity cannot be used as proof of a native 3D Euler solver.

The `experiment/pipeline.py` adapter contains actual evaluators for available local Euler results and deliberately leaves native-Euler parity, convergence, physical maximum force and reveal unresolved.

## Output and package integrity

Public BLIND source ZIP never contains `private/reveal.json` or a secret nonce. Results are exported separately as `Trefoil_Max_Transfer_Force_v0.2.0_outputs.zip` with SHA-256 verification. A separate optional **PRIVATE** package is required only to install the original reveal file; do not merge with BLIND outputs.

## Status taxonomy

`ORTHODOX`: incompressible Euler equations, projection, pressure Poisson, Kelvin-compatible fluid evolution under the declared body force. `DERIVED`: code-level finite-difference/FFT diagnostics, candidate residuals and Euler similarity scaling. `RESEARCH-TRACK`: stable trefoil or size-independent maximum transferable force; presently **UNRESOLVED**.

### Additional sources

1. P. G. Saffman (1992), *Vortex Dynamics*, Cambridge University Press. DOI:10.1017/CBO9780511624063.
2. T. Y. Hou and R. Li (2008), *Numerical study of nearly singular solutions of the 3-D incompressible Euler equations*, *Communications in Partial Differential Equations*, arXiv:physics/0608126.
3. X. Zhao et al. (2021), *Direct numerical and large-eddy simulation of trefoil knotted vortices*, *Journal of Fluid Mechanics*.
4. G. W. Gibbons (2002), *The Maximum Tension Principle in General Relativity*, *Foundations of Physics* 32, 1891--1901. DOI:10.1023/A:1022370717626.
