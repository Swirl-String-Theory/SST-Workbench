from __future__ import annotations

from dataclasses import replace
import math
import numpy as np

from .models import FourierComponent, IdealLink
from .fourier import evaluate


def active_mode_max_component(component: FourierComponent, amplitude_floor: float = 0.0) -> int:
    amplitude = np.sqrt(np.sum(component.A**2 + component.B**2, axis=1))
    active = np.flatnonzero(amplitude > float(amplitude_floor))
    return int(active.max()) if active.size else 0


def active_mode_max_link(link: IdealLink, amplitude_floor: float = 0.0) -> int:
    return max(active_mode_max_component(c, amplitude_floor) for c in link.components)


def next_power_of_two(value: int) -> int:
    value = max(1, int(value))
    return 1 << int(math.ceil(math.log2(value)))


def nyquist_min_samples(active_mode: int) -> int:
    # Strictly greater than 2*m avoids placing the highest source mode on the even-grid Nyquist bin.
    return max(16, 2*int(active_mode) + 2)


def nonlinear_geometry_recommended_samples(active_mode: int, oversample: float = 4.0) -> int:
    # Curvature is nonlinear in r' and r''.  Four samples per highest Fourier oscillation is a
    # conservative *numerical* floor; the convergence audit remains authoritative.
    return next_power_of_two(max(16, int(math.ceil(float(oversample)*max(active_mode, 1)))))


def truncate_component(component: FourierComponent, cutoff: int) -> FourierComponent:
    cutoff = max(0, min(int(cutoff), component.A.shape[0]-1))
    return FourierComponent(
        index=component.index,
        declared_length=component.declared_length,
        A=np.ascontiguousarray(component.A[:cutoff+1].copy()),
        B=np.ascontiguousarray(component.B[:cutoff+1].copy()),
    )


def truncate_link(link: IdealLink, cutoff: int) -> IdealLink:
    return IdealLink(
        link_id=link.link_id,
        conway=link.conway,
        diameter=link.diameter,
        components=tuple(truncate_component(c, cutoff) for c in link.components),
    )


def component_derivative_power(component: FourierComponent, derivative: int) -> np.ndarray:
    amplitude2 = np.sum(component.A**2 + component.B**2, axis=1)
    n = np.arange(len(amplitude2), dtype=float)
    if derivative == 0:
        weight = np.ones_like(n)
    else:
        weight = n**(2*int(derivative))
        weight[0] = 0.0
    return amplitude2*weight


def _periodic_integral(values: np.ndarray) -> float:
    return float(np.mean(np.asarray(values, dtype=float))*2.0*np.pi)


def analytic_component_length_bending(component: FourierComponent, sample_n: int) -> tuple[float, float]:
    sample_n = int(sample_n)
    t = np.arange(sample_n, dtype=float)*(2.0*np.pi/sample_n)
    d1 = evaluate(component, t, 1)
    d2 = evaluate(component, t, 2)
    speed = np.linalg.norm(d1, axis=1)
    curvature = np.linalg.norm(np.cross(d1, d2), axis=1)/np.maximum(speed**3, 1e-300)
    return _periodic_integral(speed), _periodic_integral(curvature**2*speed)


def analytic_link_length_bending(link: IdealLink, sample_n: int) -> tuple[float, float]:
    lengths=[]; bendings=[]
    for component in link.components:
        L, B = analytic_component_length_bending(component, sample_n)
        lengths.append(L); bendings.append(B)
    return float(sum(lengths)), float(sum(bendings))


def _cutoff_list(link: IdealLink, configured: list[int] | None) -> list[int]:
    full = active_mode_max_link(link)
    if configured is None:
        configured = [32, 64, 96, 128, 160, 192, 224]
    values = sorted({int(x) for x in configured if 0 < int(x) < full})
    values.append(full)
    return values


def spectral_tail_audit(link: IdealLink, cfg: dict | None = None) -> dict:
    cfg = dict(cfg or {})
    coefficient_resolution = float(cfg.get('source_coefficient_resolution', 1.0e-6))
    quantization_halfstep = 0.5*coefficient_resolution
    suspect_multiplier = float(cfg.get('spectral_precision_suspect_multiplier', 5.0))
    suspect_amplitude = suspect_multiplier*quantization_halfstep
    reference_cutoff = int(cfg.get('spectral_reference_cutoff', 192))
    cutoffs = _cutoff_list(link, cfg.get('spectral_cutoffs'))
    integration_oversample = float(cfg.get('spectral_integration_oversample', 8.0))
    integration_min_n = int(cfg.get('spectral_integration_min_n', 1024))
    tail_sensitivity_tol = float(cfg.get('spectral_tail_bending_relative_tolerance', 0.05))
    precision_power_tol = float(cfg.get('spectral_precision_d2_power_fraction_tolerance', 0.005))

    component_rows=[]
    total_d2=0.0; total_d2_tail_ref=0.0; total_d2_suspect=0.0
    for c in link.components:
        amp = np.sqrt(np.sum(c.A**2+c.B**2, axis=1))
        p2 = component_derivative_power(c, 2)
        n = np.arange(len(amp))
        total=float(p2.sum())
        tail=float(p2[n>reference_cutoff].sum())
        suspect=float(p2[(amp>0.0)&(amp<=suspect_amplitude)].sum())
        total_d2 += total; total_d2_tail_ref += tail; total_d2_suspect += suspect
        component_rows.append({
            'component': int(c.index),
            'active_mode_max': active_mode_max_component(c),
            'coefficient_amplitude_max': float(amp.max()),
            'nonzero_coefficient_mode_count': int(np.sum(amp>0.0)),
            'd2_power_tail_fraction_above_reference': float(tail/max(total,1e-300)),
            'd2_power_precision_suspect_fraction': float(suspect/max(total,1e-300)),
        })

    cutoff_rows=[]
    full_mode=active_mode_max_link(link)
    for cutoff in cutoffs:
        filtered=truncate_link(link, cutoff)
        integration_n=next_power_of_two(max(integration_min_n, int(math.ceil(integration_oversample*max(cutoff,1)))))
        length,bending=analytic_link_length_bending(filtered, integration_n)
        cutoff_rows.append({
            'cutoff_mode': int(cutoff),
            'is_full_source': bool(cutoff==full_mode),
            'integration_sample_n': int(integration_n),
            'length_over_D': float(length/max(link.diameter,1e-300)),
            'bending_times_D': float(bending*link.diameter),
        })

    full_row=cutoff_rows[-1]
    ref_candidates=[x for x in cutoff_rows if x['cutoff_mode']<=reference_cutoff]
    ref_row=ref_candidates[-1] if ref_candidates else cutoff_rows[0]
    bend_rel=abs(full_row['bending_times_D']-ref_row['bending_times_D'])/max(abs(full_row['bending_times_D']),1e-300)
    length_rel=abs(full_row['length_over_D']-ref_row['length_over_D'])/max(abs(full_row['length_over_D']),1e-300)
    d2_tail_fraction=float(total_d2_tail_ref/max(total_d2,1e-300))
    suspect_fraction=float(total_d2_suspect/max(total_d2,1e-300))
    tail_sensitive=bool(bend_rel>tail_sensitivity_tol)
    precision_risk=bool(suspect_fraction>precision_power_tol)
    contaminated_risk=bool(tail_sensitive and precision_risk)

    return {
        'link_id': link.link_id,
        'source_active_mode_max': int(full_mode),
        'strict_nyquist_min_sample_n': nyquist_min_samples(full_mode),
        'recommended_nonlinear_geometry_sample_n': nonlinear_geometry_recommended_samples(full_mode),
        'source_coefficient_resolution_assumed': coefficient_resolution,
        'precision_suspect_amplitude_threshold': suspect_amplitude,
        'reference_cutoff_mode_requested': reference_cutoff,
        'reference_cutoff_mode_used': int(ref_row['cutoff_mode']),
        'cutoff_rows': cutoff_rows,
        'component_rows': component_rows,
        'full_vs_reference_length_relative_difference': float(length_rel),
        'full_vs_reference_bending_relative_difference': float(bend_rel),
        'aggregate_d2_power_tail_fraction_above_reference': d2_tail_fraction,
        'aggregate_d2_power_precision_suspect_fraction': suspect_fraction,
        'spectral_tail_sensitive': tail_sensitive,
        'source_precision_risk': precision_risk,
        'spectral_tail_contaminated_risk': contaminated_risk,
        'status': (
            '[NUMERICAL] Analytic-Fourier derivative audit. spectral_tail_contaminated_risk is a risk flag, '
            'not proof that high modes are spurious. Six-decimal source coefficients can amplify under n^2 weighting.'
        ),
    }


class SpectralSamplingError(ValueError):
    """Raised before QM/Hessian work when the working Fourier geometry is under-resolved."""


def _effective_qm_sample_n(active: int, cfg: dict) -> tuple[int, dict]:
    configured = int(cfg.get('qm_sample_n', 96))
    nyquist = nyquist_min_samples(active)
    recommended = nonlinear_geometry_recommended_samples(
        active, float(cfg.get('spectral_nonlinear_oversample', 4.0))
    )
    sampling_policy = str(cfg.get('spectral_sampling_policy', 'fixed')).lower()
    if sampling_policy == 'fixed':
        effective = configured
        reason = 'configured-fixed'
    elif sampling_policy == 'auto-nyquist':
        effective = max(configured, nyquist)
        reason = 'auto-promoted-to-strict-nyquist' if effective != configured else 'configured-already-sufficient'
    elif sampling_policy == 'auto-nonlinear':
        effective = max(configured, recommended)
        reason = 'auto-promoted-to-nonlinear-floor' if effective != configured else 'configured-already-sufficient'
    else:
        raise ValueError(
            f"Unknown spectral_sampling_policy={sampling_policy!r}; expected fixed, auto-nyquist, or auto-nonlinear"
        )
    cap = cfg.get('spectral_auto_max_sample_n')
    cap_exceeded = False
    if cap is not None and effective > int(cap):
        cap_exceeded = True
    return int(effective), {
        'configured_qm_sample_n': int(configured),
        'effective_qm_sample_n': int(effective),
        'strict_nyquist_min_sample_n': int(nyquist),
        'recommended_nonlinear_geometry_sample_n': int(recommended),
        'sampling_policy': sampling_policy,
        'sampling_resolution_reason': reason,
        'spectral_auto_max_sample_n': None if cap is None else int(cap),
        'spectral_auto_cap_exceeded': bool(cap_exceeded),
    }


def prepare_qm_link(link: IdealLink, cfg: dict, enforce: bool = True) -> tuple[IdealLink, dict]:
    """Return the working Fourier geometry and a pre-computation sampling guard.

    v0.3.5 fixes the v0.3.4 control-flow bug where a raw high-mode link could run an expensive
    sub-Nyquist Hessian and only be rejected afterwards.  The guard is now usable as a campaign
    preflight, and automatic promotion is explicit rather than silent filtering.
    """
    cutoff = cfg.get('spectral_cutoff_mode')
    working = truncate_link(link, int(cutoff)) if cutoff is not None else link
    active = active_mode_max_link(working)
    effective_n, resolved = _effective_qm_sample_n(active, cfg)
    nyquist = int(resolved['strict_nyquist_min_sample_n'])
    recommended = int(resolved['recommended_nonlinear_geometry_sample_n'])
    strict_ok = bool(effective_n >= nyquist)
    nonlinear_ok = bool(effective_n >= recommended)
    cap_ok = not bool(resolved['spectral_auto_cap_exceeded'])
    policy = str(cfg.get('spectral_guard_policy', 'error')).lower()
    unresolved = (not strict_ok) or (not nonlinear_ok) or (not cap_ok)

    if enforce and policy == 'error' and unresolved:
        suggestions = []
        if cutoff is None:
            suggestions.append(
                f"use spectral_sampling_policy='auto-nonlinear' (needs N={recommended}) for the raw source"
            )
            suggestions.append(
                "or explicitly use a preregistered spectral-cutoff config (Research Track numerical regularization)"
            )
        else:
            suggestions.append(f"raise qm_sample_n to at least {recommended} for cutoff m<={int(cutoff)}")
        if not cap_ok:
            suggestions.append(
                f"raise spectral_auto_max_sample_n above {effective_n} or lower the requested working bandwidth"
            )
        raise SpectralSamplingError(
            f"{link.link_id}: spectral QM preflight rejected working geometry before Hessian evaluation. "
            f"configured N={resolved['configured_qm_sample_n']}, effective N={effective_n}, "
            f"active mode={active}, strict Nyquist floor={nyquist}, nonlinear floor={recommended}, "
            f"cutoff={cutoff}, sampling_policy={resolved['sampling_policy']}. " + '; '.join(suggestions)
        )

    return working, {
        'source_link_id': link.link_id,
        'source_active_mode_max': active_mode_max_link(link),
        'spectral_cutoff_mode': None if cutoff is None else int(cutoff),
        'working_active_mode_max': int(active),
        'qm_sample_n': int(effective_n),  # compatibility alias: now means actual N used
        **resolved,
        'strict_nyquist_pass': strict_ok,
        'nonlinear_geometry_sampling_pass': nonlinear_ok,
        'guard_policy': policy,
        'readiness_blocked': bool(unresolved),
        'precomputation_safe': bool(not unresolved),
        'status': (
            '[NUMERICAL] v0.3.5 pre-computation sampling guard. Automatic N-promotion never changes Fourier '
            'coefficients; a cutoff, when present, remains Research Track numerical regularization and not an SST law.'
        ),
    }


def spectral_qm_preflight(link: IdealLink, cfg: dict) -> dict:
    """Cheap per-link preflight with no Biot-Savart/Hessian evaluation."""
    source_audit = spectral_tail_audit(link, cfg)
    try:
        _, guard = prepare_qm_link(link, cfg, enforce=False)
        unresolved = bool(guard['readiness_blocked'])
        guard_error = None
        if str(cfg.get('spectral_guard_policy', 'error')).lower() == 'error' and unresolved:
            try:
                prepare_qm_link(link, cfg, enforce=True)
            except SpectralSamplingError as exc:
                guard_error = str(exc)
    except Exception as exc:
        return {
            'link_id': link.link_id,
            'pass': False,
            'error': f'{type(exc).__name__}: {exc}',
            'status': '[NUMERICAL] spectral preflight failed before QM computation.',
        }
    return {
        'link_id': link.link_id,
        'pass': bool(not unresolved),
        'guard': guard,
        'source_tail_risk': bool(source_audit['spectral_tail_contaminated_risk']),
        'source_active_mode_max': int(source_audit['source_active_mode_max']),
        'source_precision_risk': bool(source_audit['source_precision_risk']),
        'guard_error': guard_error,
        'status': (
            '[NUMERICAL] Cheap preflight. pass concerns working-geometry sampling only; source-tail risk is reported '
            'separately and can still block physics interpretation.'
        ),
    }
