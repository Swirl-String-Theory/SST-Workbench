# Swirl Clock observables

v0.1.1 treats the Swirl Clock as a set of measured eigenmode/transport observables, not as an imposed clock law.

For a selected finite-core mode

\[
\lambda=\Re\lambda+i\Im\lambda,
\]

the exported CLOSED-case fields are:

| field | definition | role |
|---|---|---|
| `lambda_real` | \(\Re\lambda\) | exponential growth/decay rate |
| `lambda_imag` | \(\Im\lambda\) | signed modal phase frequency |
| `omega_mode` | \(|\Im\lambda|\) | positive clock tick rate |
| `T_mode` | \(2\pi/|\Im\lambda|\) | eigenmode period |
| `group_velocity` | \(d\omega/dk\) | propagation speed of the tracked branch |
| `tau_loop_group` | \(L/|v_g|\) | group-delay prediction |
| `tau_return_measured` | first coherent packet return | independently measured loop time |
| `phi_loop` | phase at measured return | feedback-loop phase output |
| `omega_swirl_rms_core` | core-weighted RMS of \(V_\theta/r\) for \(r\le a\) | base-flow material swirl scale |
| `mode_over_swirl_frequency_ratio` | \(|\Im\lambda|/\Omega_{\rm swirl,rms}\) | dimensionless clock-lock ratio |

The solver internally writes `omega = -Im(lambda)` because of its normal-mode sign convention; `lambda_imag` is exported explicitly to remove that ambiguity.

## Conservative stability target

For an inviscid ideal-fluid mechanism the primary target is

\[
\boxed{\Re\lambda\approx0,\quad \Im\lambda\neq0,}
\]

not an arbitrary negative damping rate.

## Phase-delay hypothesis

The measurable hypothesis is

\[
\phi_{\rm loop}=\phi(\Im\lambda,\tau_{\rm return})
\quad\stackrel{?}{\Longrightarrow}\quad
\Re\lambda\downarrow.
\]

No `tau_delay`, `feedback_delay`, preferred return time, or phase controller exists in the dynamics.
