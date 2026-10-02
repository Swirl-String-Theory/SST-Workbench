from __future__ import annotations
import math
import numpy as np
from .kernels import velocity
from .geometry import spacing_metrics, reparameterize


def rhs(X, offs, gamma, core, require_native=False):
    return velocity(X, offs, gamma, core, require_native)


def rk4(X, dt, offs, gamma, core, require_native=False):
    k1 = rhs(X, offs, gamma, core, require_native)
    k2 = rhs(X + 0.5 * dt * k1, offs, gamma, core, require_native)
    k3 = rhs(X + 0.5 * dt * k2, offs, gamma, core, require_native)
    k4 = rhs(X + dt * k3, offs, gamma, core, require_native)
    return X + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)


def _dynamic_step_budget(X, offs, gamma, cfl, T, cfg):
    sm = spacing_metrics(X, offs)
    dt0 = 4 * math.pi * cfl * sm["ds_min"] ** 2 / max(abs(gamma), 1e-300)
    nominal = int(math.ceil(T / max(dt0, 1e-300)))
    static = int(cfg.get("max_substeps", 200000))
    if not bool(cfg.get("dynamic_max_substeps", True)):
        return static, nominal, dt0
    safety = float(cfg.get("max_substeps_safety_factor", 8.0))
    absolute = int(cfg.get("max_substeps_absolute", max(static, 1000000)))
    budget = max(static, int(math.ceil(max(1, nominal) * safety)))
    budget = min(budget, absolute)
    return budget, nominal, dt0


def evolve(X0, offs, cfg, sample_count=256, cfl_divisor=1.0):
    """Adaptive RK4 with fixed physical dimensionless horizon and mesh-gauge control.

    v0.3.1 adds adaptive arclength reparameterization.  The operation changes
    marker parametrization, not the represented centerline geometry, and is
    triggered only by preregistered mesh-quality diagnostics.
    """
    X = np.asarray(X0, float).copy()
    gamma = float(cfg["gamma_dimensionless"])
    core = float(cfg["core_fraction"])
    T = float(cfg["t_final"])
    cfl = float(cfg["stability_cfl"]) / float(cfl_divisor)
    req = bool(cfg.get("require_native", False))
    reps = int(cfg.get("reparameterization_events", 0))

    adaptive = bool(cfg.get("adaptive_reparameterization", True))
    cv_trigger = float(cfg.get("adaptive_reparam_cv_trigger", 0.12))
    edge_trigger = float(cfg.get("adaptive_reparam_edge_ratio_trigger", 2.0))
    check_every = max(1, int(cfg.get("adaptive_reparam_check_every", 1)))

    maxsteps, nominal_steps, initial_dt_target = _dynamic_step_budget(
        X, offs, gamma, cfl, T, cfg
    )

    sample_times = np.linspace(0, T, max(16, int(sample_count)))
    rep_times = np.linspace(0, T, reps + 2)[1:-1] if reps > 0 else np.array([])
    event_times = np.unique(np.concatenate([sample_times, rep_times, [T]]))

    samples = [X.copy()]
    times = [0.0]
    sample_diags = [spacing_metrics(X, offs)]
    nsteps = 0
    dtmin = float("inf")
    dtmax = 0.0
    t = 0.0
    adaptive_count = 0
    scheduled_count = 0
    mesh_cv_max_observed = float(sample_diags[0]["ds_cv"])
    mesh_edge_ratio_max_observed = float(sample_diags[0]["edge_ratio"])
    mesh_cv_max_post_reparam = float(sample_diags[0]["ds_cv"])

    for target in event_times[1:]:
        while t < target - 1e-15 * max(1.0, T):
            sm = spacing_metrics(X, offs)
            dt_target = 4 * math.pi * cfl * sm["ds_min"] ** 2 / max(abs(gamma), 1e-300)
            dt = min(dt_target, target - t)
            if not np.isfinite(dt) or dt <= 0:
                raise RuntimeError("invalid adaptive timestep")
            X = rk4(X, dt, offs, gamma, core, req)
            t += dt
            nsteps += 1
            dtmin = min(dtmin, dt)
            dtmax = max(dtmax, dt)

            if nsteps > maxsteps:
                raise RuntimeError(
                    f"max_substeps exceeded: >{maxsteps}; "
                    f"nominal_initial_steps={nominal_steps}, T={T:.12g}"
                )

            if adaptive and (nsteps % check_every == 0):
                sm_after = spacing_metrics(X, offs)
                mesh_cv_max_observed = max(mesh_cv_max_observed, float(sm_after["ds_cv"]))
                mesh_edge_ratio_max_observed = max(
                    mesh_edge_ratio_max_observed, float(sm_after["edge_ratio"])
                )
                if (
                    sm_after["ds_cv"] > cv_trigger
                    or sm_after["edge_ratio"] > edge_trigger
                ):
                    X, o2 = reparameterize(X, offs)
                    if not np.array_equal(o2, offs):
                        raise RuntimeError("component offsets changed during adaptive reparameterization")
                    adaptive_count += 1
                    sm_post = spacing_metrics(X, offs)
                    mesh_cv_max_post_reparam = max(
                        mesh_cv_max_post_reparam, float(sm_post["ds_cv"])
                    )

        if len(rep_times) and np.min(np.abs(rep_times - target)) < 1e-12 * max(1, T):
            sm_pre = spacing_metrics(X, offs)
            mesh_cv_max_observed = max(mesh_cv_max_observed, float(sm_pre["ds_cv"]))
            mesh_edge_ratio_max_observed = max(
                mesh_edge_ratio_max_observed, float(sm_pre["edge_ratio"])
            )
            X, o2 = reparameterize(X, offs)
            if not np.array_equal(o2, offs):
                raise RuntimeError("component offsets changed during scheduled reparameterization")
            scheduled_count += 1
            sm_post = spacing_metrics(X, offs)
            mesh_cv_max_post_reparam = max(
                mesh_cv_max_post_reparam, float(sm_post["ds_cv"])
            )

        if np.min(np.abs(sample_times - target)) < 1e-12 * max(1, T):
            sm_sample = spacing_metrics(X, offs)
            mesh_cv_max_observed = max(mesh_cv_max_observed, float(sm_sample["ds_cv"]))
            mesh_edge_ratio_max_observed = max(
                mesh_edge_ratio_max_observed, float(sm_sample["edge_ratio"])
            )
            samples.append(X.copy())
            times.append(float(target))
            sample_diags.append(sm_sample)

    sm0 = spacing_metrics(np.asarray(X0, float), offs)
    smf = spacing_metrics(X, offs)
    return np.array(times), np.array(samples), {
        "dt_min": dtmin,
        "dt_max": dtmax,
        "n_steps": nsteps,
        "max_substeps_budget": int(maxsteps),
        "nominal_initial_steps": int(nominal_steps),
        "initial_dt_target": float(initial_dt_target),
        "initial_mesh": sm0,
        "final_mesh": smf,
        "sample_mesh_max_cv": max(float(d["ds_cv"]) for d in sample_diags),
        "sample_mesh_max_edge_ratio": max(float(d["edge_ratio"]) for d in sample_diags),
        "mesh_cv_max_observed": float(mesh_cv_max_observed),
        "mesh_edge_ratio_max_observed": float(mesh_edge_ratio_max_observed),
        "mesh_cv_max_post_reparam": float(mesh_cv_max_post_reparam),
        "adaptive_reparameterizations": int(adaptive_count),
        "scheduled_reparameterizations": int(scheduled_count),
        "adaptive_reparam_cv_trigger": float(cv_trigger),
        "adaptive_reparam_edge_ratio_trigger": float(edge_trigger),
        "cfl_divisor": float(cfl_divisor),
        "fixed_t_final": T,
    }
