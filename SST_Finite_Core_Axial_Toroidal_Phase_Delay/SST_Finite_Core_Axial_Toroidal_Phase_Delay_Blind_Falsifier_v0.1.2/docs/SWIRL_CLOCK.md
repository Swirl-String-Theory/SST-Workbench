# Swirl Clock observables — v0.1.2

The Swirl Clock is a measured set of finite-core eigenmode and transport observables.  It is not an imposed clock law.

For

\[
\lambda=\Re\lambda+i\Im\lambda,
\]

v0.1.2 exports:

| field | definition / meaning |
|---|---|
| `lambda_real` | \(\Re\lambda\), exponential growth/decay rate |
| `lambda_imag` | \(\Im\lambda\), signed lab-frame modal phase frequency |
| `omega_mode` | \(|\Im\lambda|\) |
| `T_mode` | \(2\pi/|\Im\lambda|\) |
| `advective_frequency_mode_weighted` | energy-weighted \(\langle mV_\theta/r+kU_s\rangle_E\) |
| `omega_intrinsic` | \(\omega-\omega_{adv}\), co-moving/internal frequency |
| `T_intrinsic` | \(2\pi/|\omega_{intrinsic}|\) |
| `group_velocity` | \(d\omega/dk\) of the tracked branch |
| `tau_loop_group` | \(L/|v_g|\) |
| `tau_return_measured` | continuously refined packet-envelope return |
| `phi_loop` | carrier phase at that refined return |
| `phase_uncertainty_rad` | combined return-time + dispersion phase uncertainty |
| `phase_sampling_step_rad` | local phase resolution used by the refinement |
| `dispersion_omega_rmse` | local branch-frequency polynomial fit RMSE |
| `carrier_phase_cycles_at_return` | \(|\Im\lambda|\tau_{ret}/2\pi\) |
| `omega_swirl_rms_core` | RMS material \(V_\theta/r\) clock in the core |
| `mode_over_swirl_frequency_ratio` | \(|\Im\lambda|/\Omega_{swirl}\) |
| `intrinsic_over_swirl_frequency_ratio` | \(|\omega_{intrinsic}|/\Omega_{swirl}\) |
| `clock_regime` | FAST_SWIRL_LOCKED / SLOW_MODE / OTHER_BRANCH |

## Why phase and delay have separate validity gates

The packet envelope can return at the predicted group delay even if its absolute carrier phase is uncertain.  Over a long loop,

\[
\delta\phi_{disp}\sim \sigma_\omega\tau_{ret}.
\]

Therefore:

\[
\text{delay valid}\centernot\Rightarrow\text{phase valid}.
\]

This separation is a core v0.1.2 integrity rule.

## Conservative stability target

For the inviscid mechanism the clean target remains

\[
\Re\lambda\rightarrow0,\qquad |\Im\lambda|>0,
\]

not arbitrary dissipative decay.
