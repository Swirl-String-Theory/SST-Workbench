# A050 v0.3.2 design rationale

The v0.3.0 result is not treated as a failed branch-selection experiment. Its failure is specifically a failure of the preregistered stationary modal-persistence definition. The observed recurrent branch label survives across all primary baselines and holdouts, while the checkpoint phase-rate estimate varies strongly and can change sign.

v0.3.2 therefore keeps the v0.3.0 verdict frozen and asks a narrower falsifiable diagnostic question: can a dynamically selected branch remain topologically/modal-identical while its phase clock is nonstationary?

A sign reversal of angular phase rate is not automatically incoherent. If the unwrapped phase remains locally well described by linear segments, the branch remains stable, and significant local angular-rate segments change sign, v0.3.2 classifies the trajectory as `COHERENT_REVERSING`. Random or poorly resolved phase remains `INCOHERENT_OR_UNRESOLVED`.

Because the diagnostic was designed after inspecting v0.3.0, any positive v0.3.2 pattern should be used to define a future independent confirmatory panel rather than promoted directly to theory validation.
