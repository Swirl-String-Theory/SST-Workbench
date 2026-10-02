# U(q) experiment — twisted vortex ring speed deficit

**Purpose.** Fix the prefactor of the effective Kirchhoff twist stiffness of a vortex
filament, C_eff = c\* ρΓ²a², by an independent, grid-level measurement, and
discriminate between core models:

| model | C_eff | ring-speed deficit ΔU = U(0) − U(q) |
|---|---|---|
| A: uniform-vorticity (Rankine) core, uniform vortex-line twist q | ρΓ²a²/12π | Γa²q²/12πR₀ |
| B: hollow core, sheet twist | ρΓ²a²/4π | Γa²q²/4πR₀ |

Both satisfy the Moffatt–Ricca constraint H = Γ²Tw identically, so helicity cannot
distinguish them; the *energy* (equivalently the ring speed, via U = ∂E/∂P) can.
The analytic route is the Saffman core constant: the axial-flow term
−(8π²/Γ²)∫w²r′dr′ in the ring-speed formula, which was shown (Hamiltonian check)
to be exactly the image of the axial-flow kinetic energy ½ρ∫w²dV under Kelvin-conserved
stretching. Then ΔU = −C_eff q²/(ρΓR).

**Independence of the test.** The solver (`axisym_solver.py`) integrates the
axisymmetric incompressible Euler equations with swirl on an (r,z) grid
(vorticity–streamfunction form, σ = r·u_φ and η = ω_φ/r advected, centrifugal source
(1/r⁴)∂z σ², DST/Thomas Poisson solve, SSP-RK3, ν = 5·10⁻⁵ for stability,
Re_Γ = 2·10⁴). No filament asymptotics, no LIA, no Saffman formula enters the
dynamics. For a vortex *ring*, axial core flow = u_φ (toroidal jet), and a toroidal
jet makes the vortex lines helices around the torus — i.e. exactly core twist; the
q ↔ w map for model A is w(s) = (qΓ/2π)(1 − s²/a²).

**Setup.** Γ = 1, R₀ = 1, a = 0.18 (ε = 0.18), tanh-smoothed top-hat core
(edge 0.03, giving a_eff = 0.190 from the vorticity second moment), grid 256×512 on
(r,z) ∈ [0,3.5]×[0,7], T = 3.5, speed from the impulse-weighted vorticity centroid
fitted over t ∈ [0.7, 3.5]. q ∈ {0, 2.5, 3.5, 4.25, 5}. Initialized helicity is
0.915 · Γ²qR₀ (edge smoothing removes ~8.5% of the nominal twist), which is why the
profile-exact ("self-consistent") target ΔU_sc = J/(Γ·R̄), with J = ∫u_φ² dr dz
evaluated on the *evolved* fields near the ring, is the correct comparator; the
a-priori model-A line uses the nominal (a, q).

**Results** (`results_table.csv`, figure `uq_experiment.png`):

| q | ΔU measured | model A (a nominal) | self-consistent target | hollow |
|---|---|---|---|---|
| 2.5 | 0.00517 | 0.00537 | 0.00515 | 0.01611 |
| 3.5 | 0.01015 | 0.01053 | 0.01007 | 0.03158 |
| 4.25 | 0.01498 | 0.01552 | 0.01483 | 0.04657 |
| 5.0 | 0.02079 | 0.02149 | 0.02050 | 0.06446 |

Fit ΔU = k·q² through the origin: k_meas = 8.304·10⁻⁴, rms scatter 2.5·10⁻⁵
(clean q² scaling). Ratios: k_meas/k_modelA(nominal) = **0.966**;
per-point agreement with the self-consistent Saffman target ≈ **1%**;
k_meas/k_hollow = 0.322.

**Conclusions.**
1. The prefactor **C_eff = ρΓ²a²/12π is confirmed at the few-percent level** for the
   uniform-twist Rankine core, by grid-level Euler dynamics containing none of the
   asymptotic machinery. Status upgrade: derived → **numerically verified**.
2. The hollow-core value (3× larger) is excluded *for this initial condition* — as
   expected: the prefactor is a property of the core model, not of the fluid. The
   experiment validates the machinery that converts any declared core model into its
   C_eff.
3. Agreement at ~1% with the self-consistent target confirms the Saffman core-constant
   term itself (the −8π²/Γ²∫w²r′dr′ coefficient) end-to-end.

**What this does NOT decide** (open Canon decisions, unchanged):
- D1/D2: which (ρ, a) of the SST regime set enters C_eff — the vorticity-support
  radius (a_core-type) and the same density weighting as the canonical core-interior
  kinetic term. This run is single-density (ρ = 1); it cannot arbitrate ρ_core vs ρ_f.
- D3: material core (twist is a real DOF, C_eff finite as here) vs phase-defect /
  GP-like core (no independent local twist DOF; energetics via flux–torsion coupling
  only). The experiment presupposes a material core.
- 3D stability of strongly twisted cores: the axisymmetric solver suppresses
  non-axisymmetric instabilities by construction (a feature for clean measurement,
  a caveat for physical realism at swirl ratio ≈ 0.9).

**Port notes for vortexring-lab.** The simulator is a filament code (Schwarz +
Klenin–Langowski); it cannot *independently* test this — it would reproduce whatever
C_eff is fed in. Correct consumption of this result:
1. Add the Fukumoto–Miyazaki axial-flow term to the equation of motion,
   γ_t = β₀κb + β₁[½κ²t + κ′n + κτb], with β₁ tied to the core axial flux; twist/flux
   per filament becomes a state variable (natural hook: the existing `coreFlow` /
   `coreFlowLock` machinery).
2. Carry twist energy E_Tw = ½C_eff∫q²ds with C_eff = ρΓ²a_core²/12π conditional on
   the D1/D2/D3 Canon decisions; keep the prefactor tagged `[core-model: Rankine
   uniform-twist, verified]`.
3. Parity check for the port: reproduce ΔU/U(0) = −C_eff q²/(ρΓR·U(0)) for a single
   ring against `results_table.csv` before canonization (same gate discipline as WB-0.1).

**Files.** `axisym_solver.py` (solver), `run_experiment.py` (per-q runner:
`python3 run_experiment.py <q> [<q> ...]`), `collect_and_plot.py` (analysis/figure),
`tier1_static_checks.py` (algebraic validation of C_eff and H = Γ²Tw for both core
models, machine precision), `run_q*.json` (raw traces incl. Z(t), R(t), J(t)).
