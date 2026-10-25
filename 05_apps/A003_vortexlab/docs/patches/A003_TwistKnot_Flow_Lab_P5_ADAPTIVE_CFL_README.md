# A003 TwistKnot Flow Lab P5 — Adaptive CFL Precision Gate

**Status:** NUMERIC SAFETY PATCH / NOT PHYSICS CERTIFICATION.

## Root cause
The P2 gate rejected all `dt < 1e-6 s` regardless of validity. The reported `dt=1.9034355272012943e-7 s` is a finite, positive CFL step and must not be forced upward or automatically rejected.

## Change
- `safeStep` accepts finite positive dt if `tPhys + signed_dt != tPhys` in IEEE-754 FP64 arithmetic. Rejects invalid, nonfinite or numerically unresolvable time advance.
- Active simulation loop passes its actual absolute simulation clock to the gate, including reverse-time runs.
- Preserve the CFL law, contact guard, RK4 integrator and rollback; do **not** change gamma, vortex radius, seed, or solver resolution.
- Twist Flow reports sub-microsecond timesteps and the theoretical number of steps per simulated second. This is a performance warning, not a false physical closure.
- Core-qualification warning `SUB_PRECISION_CORE` remains separate.

## Cautions
- Tiny dt can require millions to billions of steps per simulated second, especially full Biot–Savart at native N=1024. A higher playback speed does not remove CPU cost.
- A core of `1e-18 m` can be representable as input, but at centimeter geometry it cannot be independently resolved by FP64 contact detection. Do not interpret this as a certified physical core.
- This patch does not add 3D Euler pressure, wall Neumann boundary, or finite-core dynamics.

## Install
Apply the overlay to the P4 `A003_vortexlab` folder, replacing files of the same relative path. Preserve the existing folder. For independent install use the complete P5 ZIP.
`npm run check` then `npm start`, open `http://127.0.0.1:4173/twist-flow/`.

## P4 parent hashes
- runtime sha256: `13ccbb662a537c712610cc168d3903da64086af95e00dbebdcb31cb7404aa28b`
- qualification module sha256: `4abcd1cafadbfa7b690deb06b96fac6b7623f8f2da9ac857f4c916554e40e907`
