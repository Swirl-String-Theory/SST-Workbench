# A065 v0.3.7 Finite-Core Science Contract
FINITE_CORE_V037_PREREG_SHA256=486414f5da90661ca5e13123f44290a3651ccac26ab71d260591656947f88429

Hypotheses: H0 = circulation and vorticity-free centerline geometry do not uniquely determine a physical vortex core or a universal regularization cutoff. H1 = given a separately sourced core-vorticity profile plus circulation and enstrophy, a profile-specific core width can be identified independently of held-out velocity, and a kernel-equivalent epsilon may or may not predict held-out dynamics.

## Precommitted inference (synthetic analytic controls ONLY)
Gaussian: omega(r)=Gamma/(pi*a^2)*exp(-(r/a)^2); Z=int omega^2 dA=Gamma^2/(2*pi*a^2). Rankine: omega(r)=Gamma/(pi*a^2) for r<=a, zero outside; Z=Gamma^2/(pi*a^2). Thus a_G=Gamma/sqrt(2*pi*Z) and a_R=Gamma/sqrt(pi*Z). Cross-sectional enstrophy Z is per filament length, not the 3-D total.

The velocity is v_theta(r)=Gamma_enclosed(r)/(2*pi*r). Rosenhead v_RM(r)=Gamma*r/(2*pi*(r^2+epsilon^2)); slope matching implies epsilon=a for these two parameterizations. Half-circulation matching instead implies epsilon=a*sqrt(log 2) (Gaussian) and epsilon=a/sqrt(2) (Rankine). These mappings are not equal. Predict held-out velocity and pressure gradient rho*v^2/r without any fit to those values.

G22 source integrity & three original seal roots: FAIL closed on modification.
G23 analytic profile-conditional inverse from Gamma/Z and wrong-profile negative controls.
G24 strict hypothesis: one slope-matched Rosenhead epsilon predicts all held-out swirl AND pressure-gradient profiles within 5% (FAIL signifies model mismatch, not software failure).
G25 epistemic diagnostic: two legitimate matching rules disagree by >10% relative epsilon for both core types.
G26 native C++17 binary64 parity, purely radial closed-form kernel.
G27 independent physical PKLSA Euler finite-vorticity core measurement: UNRESOLVED absent authenticated cross-section and independent observable.

The pressure-gradient synthetic holdout is derived from the same v_theta and is not a second independent physical measurement. This numerical self-consistency only checks Euler circular force balance, not time-dependent Euler stability, confinement, dissipation or a physical Casimir force.

Geometric KnotPlot/Fourier/Torus trefoil centerlines contain **no transverse omega(r)**. They cannot yield a measured Z, an SI core width, or the canonical SST r_c. Existing original G2/G11/G13 failures and three seals unchanged; G3/G8 and force claims unchanged. No special epsilon tuned to a force fit.
