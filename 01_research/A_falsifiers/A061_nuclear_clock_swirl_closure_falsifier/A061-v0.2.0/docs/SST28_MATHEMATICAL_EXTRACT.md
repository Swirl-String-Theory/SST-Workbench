# SST-28 mathematical extraction for A061 (not independent proof)

Source: O. Iskandarani, *Time from Swirl: A Hydrodynamic Origin of Proper Time*, original SST-28 (Jan 2026), doi:10.5281/zenodo.17877012; Google Drive `SST-28_Time_from_Swirl.pdf` revision dated Jan 27, 2026.

- Eq. (3) axisymmetric reference ansatz: angular speed `Omega_s(r)=(vchar/rc) exp(-r/rc)`, `v_theta(r)=vchar (r/rc) exp(-r/rc)`.
- Eq. (5) axial vorticity: `omega_z(r)=(vchar/rc) exp(-r/rc) (2-r/rc)`.
- Eqs. (6)-(7) local clock factor: `S(r)=sqrt(1 - [v_theta(r)/vchar]^2)`, `dt_local=S(r) dt_inf`, and `S(rc)=sqrt(1-exp(-2))≈0.929873`.
- Eq. (9) bound-state Hamiltonian ansatz: `i*hbar*dPsi/dt_inf = S(x) H[v] Psi`. Such a factor rescales a transition measured against an independently specified laboratory time, but the paper **does not derive a species-specific thorium/nuclear versus ytterbium/electron coupling**.
- Eq. (18) proposed circulation plateaus: `Gamma_C=n*kappa` for linked loops. Eq. (19) `kappa=2*pi*rc*vchar`.
- Eqs. (22)-(24) `v_theta^(n)=n*kappa/(2*pi*r)` and `S_n(r)=sqrt(1-[v_theta^(n)/vchar]^2)`. Substituting the paper's Eq. (19) at `n=1,r=rc` yields `S_1(rc)=0`; printed Eq. (24) instead gives `sqrt(1-1/(4*pi*pi))≈0.98725` if the right-hand formula as printed is used, together with an inconsistent reported numerical value `~0.9603`. The source's plateau formula and reference exponential profile are not automatically the same flow field.
- Eq. (27) adopted local time-symmetric effective swirl Lagrangian, and Eq. (29) vector Helmholtz equation (`nabla^2 v + ell_omega^-2 v=0`) under its assumptions. Those equations alone do not derive the spectroscopic Th-229 isomer transition energy.
- Eq. (38) effective metric is described in SST-28 as bookkeeping on an underlying Euclidean background; metric terms require explicit speed/time normalization before comparison to dimensional relativistic intervals.

**Caveats for A061**: The SST-28 material is theory-side provenance, not observational data. A dual-clock experiment cannot see a common time reparameterization factor without an independently distinct coupling. Circulation winding integer labels are not automatically frequency-plateau labels without a dynamical mapping. Dimensional constants are kept in a private reveal file; blind computations use normalized `x=r/rc` and `v/vchar`.
