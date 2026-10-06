from __future__ import annotations

def summarize_rpo(result: dict) -> dict:
    cand=dict(result.get('candidate',{}))
    return {
        'protocol':result.get('protocol'),
        'candidate':cand,
        'termination_reason':result.get('termination_reason'),
        'termination_time_hat':result.get('termination_time_hat'),
        'recurrence_trace':result.get('recurrence_trace',[]),
    }

def run_rpo_conditioning(orbit_module, centerline, *, D: float, cfg: dict, force_python: bool):
    r=orbit_module.search_relative_periodic_orbit(
        centerline,D=float(D),offset_over_D=float(cfg['offset_over_D']),eps_over_D=float(cfg['eps_over_D']),
        channel_phase=float(cfg['channel_phase_rad']),gamma_plus=float(cfg['gamma_plus_hat']),gamma_minus=float(cfg['gamma_minus_hat']),
        dt_hat=float(cfg['dt_hat']),max_time_hat=float(cfg['max_time_hat']),min_time_hat=float(cfg['min_time_hat']),
        snapshot_stride=int(cfg['snapshot_stride']),recurrence_tol_over_D=float(cfg['recurrence_tol_over_D']),
        force_python=bool(force_python),skip_build=True,return_trajectory=False,
    )
    return summarize_rpo(r)
