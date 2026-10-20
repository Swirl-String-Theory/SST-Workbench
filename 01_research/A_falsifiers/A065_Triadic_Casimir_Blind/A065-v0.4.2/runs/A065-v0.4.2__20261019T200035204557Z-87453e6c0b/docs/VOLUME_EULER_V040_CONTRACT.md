# A065-v0.4.0 VOLUME/EULER3D preregistered research contract

- `preregistration/VOLUME_EULER_V040.json` SHA256 is hard-coded in `triadic/volume_v040.py`, and may not be mutated without version change.
- Only exact original A003 0.2.3 adapter and original A003-v0.1.2 atlas (all 384 source records) are scientific source inputs. Atlas unavailability leaves G37,G38,G40,G42 as `NOT_RUN_PREREQUISITE`.
- The two source XYZ fingerprints are checked through the **actual original A003 parser**. After loading the 1200 original nodes, `stride=6` gives the same 200-node initialization on every grid.
- Periodic box L=12, assumed Gaussian a=0.55, Gamma=1, density=1; no parameter fit to velocity or pressure at any grid.
- `N = 48,64,96` rebuilt independently from the same original polyline. Fourier resampling only compares generated arrays at different resolutions.
- 3D Euler: `du/dt = P(u cross curl(u))`, RK4 with 2/3 dealias, 4 steps, T=0.02, periodic BC. This is inviscid incompressible Euler of a **prescribed synthetic initial condition**, NOT a physical source-native PKLSA vortex field.
- Volume and Euler field convergence is measured as relative L2 norm (u, omega, p) comparing the lower grid trigonometric interpolant against independently computed upper grid. Threshold 5% was precommitted.
- Pressure is a Poisson result of the **same numerical IVP** and is NOT a physically independent holdout. The G42 pressure convergence is a discretization check only.
- Energy drift, `div u` and Taylor-Green temporal RK4-halving are software tests, not physical certification. The Taylor-Green helicity is almost zero; **no relative helicity test** is meaningful there.
- Full source-native closure would require authenticated true initial three-dimensional vorticity (not just centerline XYZ), separately sourced physical pressure/velocity data, at least two independent providers, source-specific boundary conditions, time and spatial convergence, and *a new preregistered physical gate*. G41 is ALWAYS `UNRESOLVED` in v0.4.0.
- G2/G11/G13/G24/G29/G31/G35 historical failures and D01/D02/D03 seals remain unchanged. A successful new numerical gate is not permission to reveal blinded physical data.
