# VCCR v0.2.0 — science contract and qualification gates

## Claim boundary

**Verified:** v0.1.0 uniform circular-tube algebra, conditional SST reference calibration, and v0.2.0 numerical RK4 tracer conservation for a time-dependent **exact affine Euler field** with independent finite-difference momentum, divergence and vorticity checks; temporal order; intentionally broken Euler counterexample.

**Not verified:** finite-core vortex field, self-induced knotted Biot–Savart/Euler dynamics, material-ring extraction from native PKLSA, physical thickness, vortex reconnection, true topology invariance, shared volume across knotted species, or a physically derived Swirl Clock. No particle, gravitational or mass claims.

## Gates

| Gate | Requirement | This package |
|---|---|---|
| G0 | Original analytical state/mass/dimension regression | PASS (7 legacy tests) |
| G1 | Unforced incompressible Euler `Du/Dt = -grad(p)/rho`, `div u=0`, independent RK4 material tracers | PASS (affine exact solution only) |
| G2 | Broken rotation law fails physical laws | PASS (negative control rejected) |
| G3 | Independent tracer polygons and velocities recover `A λ`, `Gamma`, `omega` and `a_eff` | PASS (affine circular + ellipse only) |
| G4 | Native knotted finite-core Euler solution with material-particle and source identity | NOT_RUN |
| G5 | Independently computed native circulation and vorticity flux in same flow | NOT_RUN |
| G6 | Native grid spacing/time-step convergence incl. pressure Poisson, local transport | NOT_RUN |
| G7 | Topological invariants / geometric thickness / component-wise no reconnection | NOT_RUN |
| G8 | Swirl Clock internal excitation eigenfrequency from same flow | NOT_RUN |

`GN0–GN7` are separate native **data integrity** gates; even `GN2 PASS` is **measurement qualification only**, not a pass of G4–G8.

## Definitions and units

- Absolute flow time: Euler integration variable `t` (benchmark time dimensionless; external native time seconds).
- `a_eff=sqrt(A/pi)` is the **area-equivalent** radius. It is not automatically the vortex geometric reach or physical core radius.
- Native `V_proxy = A*ell` assumes a sufficiently thin/locally straight transverse material segment. Strong curvature and transverse shear require true material-cell volume/Jacobian; reject unjustified approximations.
- `Gamma_line=integral(u . dl)` is calculated using **measured** sampled velocity and marker polygon, not from the VCCR closure; independently supplied flux is never silently treated as verified.
- Different knots **cannot** share a common physical volume as an Euler deduction. This is a falsifiable optional SST hypothesis, not a law.
- Ropelength diameter convention: `R_d=L/(2*a_geo)` uses geometric thickness; `L/(2*a_core)` is physically meaningful only with measured `a_core`. Geometric thickness saturation is not assumed by new benchmark.
- `rho_f=7e-7 kg/m^3` and `rho_core=3.8934358266918687e18 kg/m^3` must never be conflated; the benchmark does not infer density.

## Native minimum evidence needed to close G4-G7

1. Same **physical** closed knotted material tube and persistent marker IDs before and after, with no remesh-induced label substitution.
2. Euler pressure, velocity, vorticity on a characterized 3D domain with boundary conditions; independent momentum, divergence and pressure–Poisson residuals.
3. Advected transverse material loops near several axial positions and measured `A(s,t)`, `lambda(s,t)`, `Gamma_line(s,t)`, and vorticity flux integral, not recovered from each other.
4. At least three distinct spatial resolutions and three time steps, with convergence of all residuals and parameter-independent tolerances.
5. Full component-wise knot/link identity and minimum clearance; monitor reconnection or crossing numerically.
6. Qualification of core geometry/profile and the correspondence of effective area radius to any physical core radius, especially at self-contact.

**Falsifier:** stable, grid-converged violation of `A(s,t)*lambda(s,t)/A(s,0)=1` or `Gamma(t)/Gamma(0)=1` within a valid material Euler vortex tube, or failure of claimed independent physical radius at fixed conserved `V` after circularity/profile gates; otherwise mark unresolved rather than modifying tolerances post-hoc.

## Countermodels explicitly tested

- At nonzero axial strain `k`, holding angular velocity `Omega` artificially constant yields nonzero Euler momentum residual and non-conserved material circulation: G2 expected FAIL for broken model, negative-control detection PASS.
- An initially **elliptical** material section satisfies area/volume/circulation scaling but has distinct major/minor radii: `a_eff` is not a unique physical radial boundary size.

## Sources

See `references.tex`. Euler/Kelvin classical fluid dynamics is established, while the specific affine test code and quantitative thresholds are new verification constructs, not discovered SST dynamics.
