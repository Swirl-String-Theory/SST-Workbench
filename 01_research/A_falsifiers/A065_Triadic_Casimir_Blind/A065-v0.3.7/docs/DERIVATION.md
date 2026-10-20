# Derivation, constraints and three-channel interpretation

This document is a research derivation and test ledger. Orthodox mathematical identities are tagged **IDENTITY**, candidate SST identifications **HYPOTHESIS**, and analytic simulator specifications **TOY**.

## A. June -> October: common dynamics, three measurement projections

Define a state `X = (u,p, theta_i, link variables, source labels)`. Observable channels must have their own units and not be added as if each were a gravitational acceleration:

1. `O_bulk`: material acceleration, circulation and pressure (units depend on observable);
2. `O_clock`: clock-ratio or path-phase comparison, transverse photon/optical measurement;
3. `O_boundary`: force or normal traction on an independently specified boundary.

This restores the June triadic diagnostics retained in SST Canon v0.8.36 §11.17. It makes no endorsement of external witness narratives.

## B. Material Euler sector [IDENTITY]

For constant material rho_M, div u=0 and `du/dt + (u.grad)u = -grad p/rho_M`, the exact pressure source is:

`Laplacian(p)=rho_M ( |curl u|^2/2 - Frobenius(strain)^2 )`,

`strain_ij=(partial_j u_i+partial_i u_j)/2`.

In D01 the 3x3 constant velocity gradient G yields u=Gx, div u=tr G, omega=curl(Gx), and `Laplacian p = -rho_M tr(G²)`. Three controls: irrotational stagnation G=diag(a,-a,0); rigid rotation; simple shear. D01 tests the exact algebra, not a resolved Euler time evolution.

## C. Conditional clock/Bernoulli relation [HYPOTHESIS + IDENTITY]

In a stationary irrotational flow `p+rho_M |u|²/2=C`. If, separately, the Canon clock hypothesis is evaluated on precisely that effective speed, `N²=1-|u|²/c_*²`, then

`N²=1+2(p-C)/(rho_M c_*²)` and `grad ln N=grad p/(rho_M c_*² N²)`.

The latter is not a generally covariant gravitational metric derivation. The statement `curl u=0` alone imposes no uniform N. Numeric clocks D01 use dimensionless c_star=3.7 selected independently of external constants.

## D. Clock plus compact connection [HYPOTHESIS]

For oriented link e=(i,j), the Canon connection rules are:

`vartheta_ij -> vartheta_ij+chi_j-chi_i`, `phi_i -> phi_i-dot chi_i`, `E_ij=-dot vartheta_ij-(phi_j-phi_i)`.

**Additional atomic-field hypothesis** (not in Canon): the physical reduced atomic clock phase transforms `theta_i -> theta_i+chi_i` and obeys `dot theta_i+phi_i=Omega_i^(0) N_i`.

A path comparison is `Theta_AB[P]=theta_B-theta_A-sum_P vartheta_e`, invariant under gauge relabelings. Its differentiated law is:

`dot Theta_AB=Omega_B N_B-Omega_A N_A+sum_P E_e`.

For two paths, their phase difference equals minus a closed-loop holonomy. D02 checks this algebra using prescribed toy phases; it does not identify actual atomic phase with the compact link group and does not prove gauge-charge matching.

## E. One-surface susceptibility [TOY, not derived PKLSA]

A 2-mode stable Hessian with M positive diagonal, symmetric positive K, and drive vector b has Euclidean-frequency scalar response:

`chi(i xi)=b^T [K+xi² M]^{-1} b`.

For an explicit bare delta-sheet stiffness `lambda_bare`, the toy effective sheet is `lambda_eff(i xi)=lambda_bare-chi(i xi)`. The current classical zero-frequency calculation uses `lambda_eff(0)` only; the other xi samples are single-body controls and **do not** enter a full nonzero-Matsubara sum. Positive lambda gives scalar reflection `r(k)=lambda/(2k+lambda)` on the imaginary/static branch. Lambda is a declared toy assumption, not derived metal reflectivity. No physical EM normalizations appear.

A genuine SST derivation must replace M, K, b and lambda_bare with independently qualified PKLSA+matter-link calculations, with all mode/gauge/continuity constraints.

## F. Two surface classical scalar interaction [TOY]

Given two nonnegative scalar reflections r1,r2, a finite-temperature classical **zero-frequency** scalar field has dimensionless free-energy and normal pressure:

`F(a,T)/A=T/(4*pi)* integral_0^infty k dk log[1-r1(k)r2(k) exp(-2 k a)]`,

`P(a,T)=-T/(2*pi)* integral_0^infty k² dk R exp(-2ka)/(1-R exp(-2ka))`, R=r1*r2.

Variable x=ka maps both integrals onto `[0,24]`; a second substitution x=t² regularizes the logarithmic integrand at the origin, using composite Simpson in t. `P=-d(F/A)/da` is checked *separately* by a fourth-order finite difference of the stored free-energy kernel against stress quadrature. The two calculations are not independent empirical measurements or independent microsolvers: they provide a conservation/implementation consistency check.

The ideal r1=r2=1 scalar benchmark (not used during BLIND) yields `F/A=-T*zeta(3)/(16*pi*a²)` and `P=-T*zeta(3)/(8*pi*a³)`. This is a **classical thermal** result, not an Euler-origin zero-temperature vacuum force. The usual ideal EM T=0 Casimir pressure instead has an `a^-4` power and quantum amplitude. Those reference numbers occur only in `private_reveal/targets.json`, which the BLIND runner hashes without reading.

## G. What can and cannot be inferred

- **Can test**: Euler vorticity/strain/Poisson algebra, a conditional clock-rate relation, gauge-invariant path phase, positive toy oscillator response, toy thermal stress/energy consistency, null decoupling and predictable temperature scaling.
- **Cannot test yet**: actual PKLSA atom-link coupling, causally propagated clock transfer, real metal dielectric response, equilibrium/vacuum statistics derived from SST, physical pressure boundary conditions, relativistic universality, Casimir-Lifshitz amplitudes, or gravity.

A signal in O_boundary alone is NOT evidence of gravity. Changing one artificial toy sheet parameter demonstrates sensitivity/identifiability, not a new physical prediction.
