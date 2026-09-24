# P2.6A/B — State-space compatibility

Drop-in pairing of C006 or A021 trajectories with an A029 radial Euler mode is undefined.

| Pack | Dynamics | Live state | Pairing with A029 \(q_m=(u_r,u_\theta,u_s,p)\) |
|---|---|---|---|
| A029-v0.4.0 | Generalized eigenproblem only; no stepper | Complex 4-block Chebyshev radial field | Target space |
| C006-v0.2.0 | RK4 regularized Biot–Savart filament | Centerline \(X\in\mathbb{R}^{N\times 3}\) | Incompatible without \(P\) |
| A021-v0.4.0 | RK2 finite-core Biot–Savart | Same centerline type | Incompatible without \(P\) |

C006 is the only backend for this attempt because `induced_velocity(targets, filament)` already evaluates off the filament. A021 is inspect-only and is not copied.

C006 helical `ring_modal_amplitudes` is a centerline projector. It is never the A029 scientific amplitude.

This pack attempts exactly one map \(P_{\rm BS}\). Integrating \(B\dot\xi=A\xi\) is forbidden: that trajectory is algebraically determined by the same eigenproblem that predicts \(\omega_m\).

`BRIDGE_REJECTED` does not falsify the A029 modal clock. It only says this filament-to-core-field bridge is not a valid independent A029-field observable.
