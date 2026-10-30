# External native Euler trajectory intake (format only; no physical certification)

Provide a genuine `.npz` written by a separately qualified Euler solver. Arrays:

- `times_s`: strictly increasing, shape `(T,)`, SI s.
- `q_m`: shape `(N,T)`, scalar pre-declared geometric observable, SI m.
- `qdot_m_s`: shape `(N,T)`, actual time derivative of q, SI m/s. Not differentiation of untracked remesh indices.
- `trial_ids`: shape `(N,)`, distinct independent physical trajectory identifiers (`dtype='<U...'`, never Python objects).
- `metadata_json`: scalar Unicode string containing JSON, with at least `solver_name`, `solver_revision`, `source_manifest_sha256`, `geometry_manifest_sha256`, `observable_definition`, `core_model`, `boundary_conditions`.

N >= 80 independent trials and T >= 12 samples are *only* preliminary format cutoffs, not evidence adequacy for Euler inference. The current adapter uses midpoint, earlier-third and future-half index sampling; all trials share the same times. The results cannot be called physically qualified without matched-state balancing, randomization, convergence and external manifest audit.

The standard experiment requires **fully coupled background filament dynamics**, not a frozen filament array. A simulation using a GP equation, reduced Biot-Savart filaments or a pinned swirl formula must declare that distinct model and cannot identify itself as an exact 3D Euler solver.

A source manifest hash is an input claim, not source-authentication proof. The official framework must later verify the file contents and numerical backend independence. If no qualified dataset is available, `run_all.cmd BASIC` remains an honest synthetic pilot.
