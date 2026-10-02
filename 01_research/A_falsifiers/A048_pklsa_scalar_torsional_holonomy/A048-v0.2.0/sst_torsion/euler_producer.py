"""Independent A047 Euler smoke producer with no invented core-phase observable.

The volumetric state can represent internal vorticity perturbations, but this
release measures only Eulerian velocity response to a displaced centerline seed.
It does not extract an advected centerline or a material/core-phase field.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import time

import numpy as np

_A047 = Path("01_research/A_falsifiers/A047_SST_Euler_Regularity_BKM_Singularity_Gate/"
             "SST_Euler_Regularity_BKM_Singularity_Gate_v0.2.0")


def _load_spectral(repo_root=None):
    if repo_root is None:
        from . import a047_spectral_reference as module
        source=Path(module.__file__)
        return module, {'source': str(_A047/'sst_bkm/spectral.py'),
            'vendored_exact_copy':True,'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
    if repo_root is None:
        candidates = [*Path(__file__).resolve().parents, Path.cwd(), *Path.cwd().parents]
        repo_root = next((p for p in candidates if (p / _A047).is_dir()), None)
    if repo_root is None:
        raise FileNotFoundError("A047 source dependency missing; supply config.repo_root")
    source = Path(repo_root) / _A047 / "sst_bkm/spectral.py"
    spec = importlib.util.spec_from_file_location("a048_a047_spectral", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, {"source": str(_A047 / "sst_bkm/spectral.py"),
                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}


def canonicalize_centerline(points, n=96, target_rms_radius=1.1):
    """A047 closed linear-arclength resampling and common similarity convention."""
    p = np.asarray(points, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) < 16 or not np.isfinite(p).all():
        raise ValueError("expected finite (M,3) centerline with M>=16")
    q = np.vstack((p, p[0]))
    segments = np.linalg.norm(np.diff(q, axis=0), axis=1)
    if np.any(segments <= 0) or int(n) < 16 or target_rms_radius <= 0:
        raise ValueError("invalid sampling, scale or degenerate centerline")
    arc = np.r_[0.0, np.cumsum(segments)]
    targets = np.linspace(0, arc[-1], int(n), endpoint=False)
    curve = np.column_stack([np.interp(targets, arc, q[:, j]) for j in range(3)])
    curve -= curve.mean(axis=0)
    rms = np.sqrt(np.mean(np.sum(curve * curve, axis=1)))
    if not np.isfinite(rms) or rms <= 0:
        raise ValueError("invalid centerline RMS radius")
    return curve * (float(target_rms_radius) / rms)


def gaussian_centerline_vorticity(points, N, L, sigma):
    """Faithful NumPy implementation of A047 centerline_vorticity_seed.

    A047 uses unweighted unit tangents at uniformly resampled stations, periodic
    minimum-image Gaussian distances and a sqrt(18)*sigma cutoff. This is an
    initializer, not an evolved filament closure. Projection subsequently makes
    the field solenoidal; the induced core differs from an exact isolated tube.
    """
    p = np.asarray(points, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3 or len(p) < 16 or not np.isfinite(p).all():
        raise ValueError("expected finite centerline (M,3), M>=16")
    if int(N) != N or N < 8 or not np.isfinite([L, sigma]).all() or min(L, sigma) <= 0:
        raise ValueError("invalid grid or core parameters")
    tangent = np.roll(p, -1, axis=0) - np.roll(p, 1, axis=0)
    norm = np.linalg.norm(tangent, axis=1)
    if np.any(norm <= 0):
        raise ValueError("degenerate tangent")
    tangent /= norm[:, None]
    coords = -0.5 * L + (np.arange(N) + 0.5) * L / N
    grid = np.stack(np.meshgrid(coords, coords, coords, indexing="ij"), axis=-1)
    omega = np.zeros((3, N, N, N), dtype=float)
    for point, unit_tangent in zip(p, tangent):
        delta = grid - point
        delta -= L * np.rint(delta / L)
        distance2 = np.sum(delta * delta, axis=-1)
        weight = np.where(distance2 <= 18 * sigma * sigma,
                          np.exp(-distance2 / (2 * sigma * sigma)), 0.0)
        omega += unit_tangent[:, None, None, None] * weight
    return omega


def _transverse_seed(curve, amplitude, mode):
    tangent = np.roll(curve, -1, axis=0) - np.roll(curve, 1, axis=0)
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    curvature = np.roll(tangent, -1, axis=0) - np.roll(tangent, 1, axis=0)
    curvature -= np.sum(curvature * tangent, axis=1)[:, None] * tangent
    norm = np.linalg.norm(curvature, axis=1)
    if np.any(norm < 1e-12):
        raise ValueError("transverse curvature-normal seed undefined at zero curvature")
    direction = curvature / norm[:, None]
    phase = 2 * np.pi * int(mode) * np.arange(len(curve)) / len(curve)
    return curve + float(amplitude) * np.cos(phase)[:, None] * direction


def core_chart_screen(curve, N, L, sigma, minimum_cells=4.0):
    """Conservative prerequisite screen; neither topology nor convergence proof."""
    from .geometry import curvature_torsion
    kappa,_,_,_=curvature_torsion(curve)
    maximum=float(np.max(kappa))
    tube_radius=3.0*sigma
    product=tube_radius*maximum
    # The chart Jacobian factor 1-r*kappa*cos(theta) must stay safely from zero.
    admissible_sigma=.5/(3.0*maximum)
    minimum_N=int(np.ceil(minimum_cells*L/admissible_sigma))
    return {'status':'PASS' if sigma*N/L>=minimum_cells and product<=.5 else 'INDETERMINATE',
            'cells_per_sigma':sigma*N/L,'required_cells_per_sigma':minimum_cells,
            'tube_radius_in_sigmas':3.0,'tube_radius_times_max_curvature':product,
            'maximum_allowed_product':.5,'max_admissible_sigma_curvature_only':admissible_sigma,
            'minimum_grid_N_curvature_and_sampling_only':minimum_N,
            'one_complex_vector_field_GiB_at_minimum_N':3*minimum_N**3*16/2**30,
            'reason':'Joint sampling and local tube-chart screen; nonlocal separation and periodic-box effects also require qualification.'}


def run_euler_smoke(points, config):
    """Return (arrays, JSON-safe report); no material-phase series is fabricated.

    Config keys: repo_root, N, L, sigma, dt, steps, amplitude, mode,
    centerline_samples, target_rms_radius, energy_drift_limit, div_rms_limit,
    minimum_cells_per_sigma. Positive core/mesh coverage does not by itself
    certify a localized tube, phase observability, or converged branch spectrum.
    """
    config = dict(config)
    if any("phase" in str(k).lower() or "torsion" in str(k).lower() for k in config):
        raise ValueError("material/core-phase input unsupported by this producer")
    N, steps = int(config.get("N", 24)), int(config.get("steps", 12))
    if N!=config.get('N',24) or steps!=config.get('steps',12):
        raise ValueError('N and steps must be integers')
    L, sigma = float(config.get("L", 2 * np.pi)), float(config.get("sigma", 0.42))
    dt = float(config.get("dt", 0.003))
    amplitude = float(config.get("amplitude", 0.005))
    mode = int(config.get("mode", 2))
    if N < 8 or N > 128 or steps < 1 or steps > 10000 or dt <= 0 or amplitude < 0 or mode < 1:
        raise ValueError("invalid bounded smoke configuration")
    if not np.isfinite([L, sigma, dt, amplitude]).all() or min(L, sigma) <= 0:
        raise ValueError("non-finite or nonpositive smoke parameter")
    spectral, dependency = _load_spectral(config.get("repo_root"))
    curve = canonicalize_centerline(points, int(config.get("centerline_samples", 96)),
                                    float(config.get("target_rms_radius", 1.1)))
    displaced = _transverse_seed(curve, amplitude, mode)
    raw_baseline = gaussian_centerline_vorticity(curve, N, L, sigma)
    raw_displaced = gaussian_centerline_vorticity(displaced, N, L, sigma)
    seed_parity={'status':'INDETERMINATE','reason':'native initializer not available'}
    try:
        import a048_seed_native
        native=np.asarray(a048_seed_native.centerline_vorticity_seed(curve,N,L,sigma,1.0))
        error=float(np.max(np.abs(native-raw_baseline)))
        relative=float(np.linalg.norm(native-raw_baseline)/max(np.linalg.norm(raw_baseline),1e-30))
        seed_parity={'status':'PASS' if relative<1e-12 else 'FAIL','max_abs_error':error,'relative_l2_error':relative}
    except ImportError:
        pass
    kx, ky, kz, k2 = spectral.wave_numbers(N, L)
    mask = spectral.dealias_mask(N, kx, ky, kz)
    # Strict cutoff removes the equality boundary that aliases when N is divisible by 3.
    modes=np.fft.fftfreq(N)*N
    strict=np.abs(modes)<N/3
    mask=mask & strict[:,None,None] & strict[None,:,None] & strict[None,None,:]
    base = spectral.velocity_from_vorticity(raw_baseline, L) * mask[None, ...]
    pert = spectral.velocity_from_vorticity(raw_displaced, L) * mask[None, ...]
    projected=np.fft.ifftn(spectral.curl_hat(base,kx,ky,kz),axes=(1,2,3)).real
    projection_change=float(np.linalg.norm(projected-raw_baseline)/np.linalg.norm(raw_baseline))
    rms = np.sqrt(np.mean(np.sum(np.fft.ifftn(base, axes=(1, 2, 3)).real ** 2, axis=0)))
    if not np.isfinite(rms) or rms <= 0:
        raise ValueError("zero or invalid initial velocity")
    base, pert = base / rms, pert / rms
    base_initial, pert_initial = base.copy(), pert.copy()
    # Fixed Eulerian probes near initial stations; these are not material tracers.
    probe_points = curve[::max(1, len(curve) // 24)]
    probe_indices = np.rint((probe_points + 0.5 * L) * N / L - 0.5).astype(int) % N
    history = {key: [] for key in ("baseline_energy", "perturbed_energy", "baseline_helicity",
                                 "perturbed_helicity", "baseline_div_rms", "perturbed_div_rms",
                                 "delta_velocity_rms", "baseline_velocity_probes",
                                 "perturbed_velocity_probes", "cfl")}
    started = time.perf_counter()
    for step in range(steps + 1):
        velocities = []
        for label, state in (("baseline", base), ("perturbed", pert)):
            velocity = np.fft.ifftn(state, axes=(1, 2, 3)).real
            vort = np.fft.ifftn(spectral.curl_hat(state, kx, ky, kz), axes=(1, 2, 3)).real
            div = np.fft.ifftn(1j * (kx * state[0] + ky * state[1] + kz * state[2])).real
            if not np.isfinite(velocity).all():
                raise FloatingPointError("Euler trajectory became non-finite")
            history[label + "_energy"].append(0.5 * np.mean(np.sum(velocity ** 2, axis=0)))
            history[label + "_helicity"].append(np.mean(np.sum(velocity * vort, axis=0)))
            history[label + "_div_rms"].append(np.sqrt(np.mean(div ** 2)))
            history[label + "_velocity_probes"].append(velocity[:, probe_indices[:, 0],
                probe_indices[:, 1], probe_indices[:, 2]].T.copy())
            velocities.append(velocity)
        history["delta_velocity_rms"].append(np.sqrt(np.mean(np.sum((velocities[1] - velocities[0]) ** 2, axis=0))))
        history["cfl"].append(max(np.linalg.norm(v, axis=0).max() for v in velocities) * dt / (L / N))
        if step < steps:
            base = spectral.rk4_step(base, dt, L, mask)
            pert = spectral.rk4_step(pert, dt, L, mask)
    arrays = {key: np.asarray(value) for key, value in history.items()}
    arrays.update(time=np.arange(steps + 1) * dt, centerline_seed=curve,
                  transverse_centerline_seed=displaced, probe_indices=probe_indices,
                  baseline_velocity_hat_initial=base_initial, perturbed_velocity_hat_initial=pert_initial,
                  baseline_velocity_hat_final=base, perturbed_velocity_hat_final=pert)
    energy_drift = max(float(np.max(np.abs(arrays[label + "_energy"] / arrays[label + "_energy"][0] - 1)))
                       for label in ("baseline", "perturbed"))
    divergence = max(float(arrays[label + "_div_rms"].max()) for label in ("baseline", "perturbed"))
    cells = sigma * N / L
    coverage = float(config.get("minimum_cells_per_sigma", 4.0))
    cfl = float(arrays["cfl"].max())
    gates = {
        "finite_fields": {"status": "PASS", "scope": "numerical smoke"},
        "energy_drift": {"status": "PASS" if energy_drift <= float(config.get("energy_drift_limit", 0.005)) else "FAIL",
                         "value": energy_drift, "limit": float(config.get("energy_drift_limit", 0.005))},
        "incompressibility": {"status": "PASS" if divergence <= float(config.get("div_rms_limit", 1e-10)) else "FAIL",
                              "value": divergence, "limit": float(config.get("div_rms_limit", 1e-10))},
        "cfl_screen": {"status": "PASS" if cfl <= 0.5 else "FAIL", "value": cfl, "limit": 0.5},
        "core_grid_coverage": {"status": "PASS" if cells >= coverage else "INDETERMINATE",
                               "cells_per_sigma": cells, "minimum": coverage,
                               "meaning": "Sampling screen only, not radial or spectral convergence"},
        "localized_core_chart":core_chart_screen(curve,N,L,sigma,coverage),
        "initializer_native_parity":seed_parity,
        "material_phase_observable": {"status": "NOT-IMPLEMENTED", "reason": "No objective material/core-phase extractor or independently seeded active core perturbation"},
        "evolved_centerline_observable": {"status": "NOT-IMPLEMENTED", "reason": "Fixed Eulerian probes are not centerline tracking"},
        "torsional_branch": {"status": "INDETERMINATE", "reason": "No phase observation or converged mode-identification window"},
    }
    return arrays, {
        "producer": "A047-v0.2.0 periodic incompressible Euler RK4",
        "dependency": dependency,
        "config": {k: v for k, v in config.items() if k != "repo_root"},
        "elapsed_evolution_seconds": time.perf_counter() - started,
        "state": "Full 3D Fourier velocity; nonlinearity P(u cross curl(u))",
        "initializer": "NumPy translation of A047 centerline_vorticity_seed; baseline-shared RMS normalization",
        "initializer_native_parity": seed_parity,
        "projection_and_bandlimit_relative_vorticity_change":projection_change,
        "dealias_policy":"strict |integer mode| < N/3; A047 equality boundary removed by adapter",
        "source_coordinate_sha256": hashlib.sha256(np.ascontiguousarray(points, dtype=np.float64).tobytes()).hexdigest(),
        "normalization_velocity_rms": float(rms),
        "prediction_inputs_consumed": [],
        "observed_response": "Fixed Eulerian velocity probes and volume RMS difference after transverse seed displacement",
        "material_phase_available": False,
        "core_phase_perturbation_available": False,
        "centerline_tracking_available": False,
        "branch_claim_allowed": False,
        "gates": gates,
        "scope": "Independent Euler producer smoke on authenticated geometry; not physical branch falsification",
        "limitations": ["Periodic finite box and projected smoothed seed", "No localized tube certification",
                        "No radial/core-radius/box-size convergence", "No resolved frequency or coherence claim",
                        "Helicity monitored; circulation/topology preservation not certified"],
    }
