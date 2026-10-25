# A003 VortexLab v7.6.25b-M1 — Fluid Qualification P2

**Status:** `NUMERICAL_SAFETY_CHECKED`, `FREE_FILAMENT_EULER_CLOSURE_UNRESOLVED`, `BOUNDARY_PRESSURE_UNRESOLVED`.

**Parent:** the exact `A003_vortexlab.zip` upload, containing `native-xyz-resolution-tracer-budget-p1`. Catalogs, original binaries, full resolution selection, shader/vendor assets, and reference copies remain untouched.

## Safety behavior and SI meaning

- The existing `a_sim` numeric input accepts **1e-18 m** as `1e-15 mm` without changing to a larger radius. `r_corePhysical` is an **independent** user-proposed parameter. They must not be conflated.
- A numerical representability gate compares `3*a_sim` with `64*Number.EPSILON * geometryScale`. For an object/cylinder of order **0.5 m**, the floor is **7.105427357601002e-15 m**. At `a_sim=1e-18 m`, a hypothetical physical core-contact distance `3e-18 m` is **NOT** spatially resolvable in the absolute-position Float64 representation. Contact uses the original numerical floor: `max(3*a_sim, floor)`. This does not claim the core has increased physically.
- `SUB_PRECISION_CORE` is an explicitly labeled **finite-core unresolved** state, even when the thin-filament line evolution itself still returns finite results. For such a state, turning off `topologyGuard` blocks integration.
- The Schwarz/Biot–Savart free filament physics, its bare self-filament kernel, and existing circulation choices are unchanged. Thus *safe parameter entry* is **not** a fully resolved nuclear-scale / attometre finite-core simulation.
- The previous silent `max(1e-6, dt)` floor is gone. If CFL (Courant–Friedrichs–Lewy condition) yields `dt<1e-6 s` or a nonfinite/nonpositive value, the UI **stops** rather than taking an unstable oversized step. This is a safe stop, not an integrator capable of nanosecond timesteps. A deeper small-step solver must be independently qualified.
- If RK4 (fourth-order Runge–Kutta) yields invalid coordinates or speeds, the candidate step is rolled back and stopped. Contact first-hit bisection also has a finite-state check.

## Independent fluid diagnostics (no hidden corrections)

- Periodic **wall normal velocity** `max |u · n|` on 12 radial-wall samples and four cap samples. Warns `NO_BOUNDARY_SOLVER`, does not impose a fake Neumann condition.
- Local **divergence** `∇·u` via central differences in the same velocity representation used by streamlines. This is a sampled numerical check, not a global incompressibility proof.
- Passive hypothetical **uniform vortex-core volume** `a_proposed(t) = a_0 sqrt(L_0/L(t))` for supplied physical core radius, not a new force or material closure.
- Explicit `NOT_IMPLEMENTED/NOT_CERTIFIED` statuses for pressure Poisson, cylindrical impermeability and velocity-vorticity curl parity/energy conservation.
- Physical viscosity-free, incompressible 3D Euler equations and pressure-boundary solver **are not implemented by this patch**. The computational model is still a free vortex filament with optional background/forcing.

## Run

From `A003_vortexlab`:

```cmd
run_all.cmd
npm start
```

Open `http://127.0.0.1:4173/`. Run `npm run test:fluid` for 19 focused P2 tests. `npm run check` also runs the inherited native catalog and provenance tests.

The original ZIP remains the rollback baseline; install this patched ZIP in a **new folder**. Do not overwrite ongoing experiment results or existing run logs. Before claiming full fluid qualification: independent 3D Euler reference solver, finite-core convergence, closed cylinder side/caps no-through boundary projection, physical pressure Poisson with Neumann compatibility, and vorticity-curl and invariant parity are required.

### Recommended runs

1. Fix knot and circulations; set `a_sim=1e-4`, `1e-8`, `1e-15`, `1e-18 m` independently. Export the model log and check `fluidQualification` and true `dtCFL`.
2. For each `a_sim`, compare native 512/1024/2048-point geometries and suitable time-step convergence. Core radius and source geometry are independent inputs.
3. For pressure and wall claims, expect **UNRESOLVED**, not PASS, until P3 implements a Neumann boundary and independent Euler reconstruction.

### References

- K. W. Schwarz (1985), *Three-dimensional vortex dynamics in superfluid helium: Homogeneous superfluid turbulence*, Physical Review B 31, 5782–5804, DOI: 10.1103/PhysRevB.31.5782.
- P. G. Saffman (1992), *Vortex Dynamics*, Cambridge University Press, DOI: 10.1017/CBO9780511624063.
