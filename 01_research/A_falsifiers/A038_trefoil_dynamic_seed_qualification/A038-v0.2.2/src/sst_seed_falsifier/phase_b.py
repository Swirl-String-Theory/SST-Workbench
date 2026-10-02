"""Full resolved-state numerical diagnostics; never a physical SST certificate.

The return action, reference volume and integration grid are FIXED while taking
derivatives. No perturbed trajectory is normalized or independently aligned.
Dense finite differences cover all 3N coordinates. Arnoldi is explicitly partial.
"""
from dataclasses import dataclass, asdict, replace
import math
import numpy as np
from scipy.linalg import null_space
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from scipy.sparse.linalg import LinearOperator, eigs, ArpackNoConvergence

from .geometry import (arclength, segment_lengths, align_cyclic,
                       min_nonlocal_vertex_distance, tangents, resample_closed)
from .solver import velocity_from_cores
from .dynamics import tangential_redistribution
from .evidence import object_sha256
from .io import geom_sha


@dataclass(frozen=True)
class FlowContract:
    n: int
    reference_length: float
    gamma: float = 1.0
    core0: float = .08
    feedback_alpha: float = 1.0
    mesh_rate: float = 4.0
    mesh_method: str = 'segment_feedback'
    mesh_cap: float = 1.0
    max_ds_cv: float = .45
    min_gap_over_ds: float = .85
    contact_skip: int = 3
    guard_stride: int = 16
    require_native: bool = True

    def __post_init__(self):
        if self.n < 8 or self.reference_length <= 0 or self.core0 <= 0 or self.guard_stride < 1:
            raise ValueError('INVALID_FLOW_CONTRACT')

    @property
    def sha256(self):
        return object_sha256(asdict(self))


@dataclass(frozen=True)
class ReturnAction:
    shift: int
    rotation: tuple
    translation: tuple

    def apply(self, x):
        return np.roll(x, self.shift, axis=0) @ np.asarray(self.rotation).T + self.translation

    @classmethod
    def fit(cls, final, initial):
        _, _, shift, rotation, translation = align_cyclic(final, initial, 1)
        return cls(shift, tuple(map(tuple, rotation)), tuple(translation))


def flow_rhs(x, contract):
    """Alpha=1 is the inherited global-volume model, alpha=0 its fixed-core ablation."""
    x = np.asarray(x, float)
    if x.shape != (contract.n, 3) or not np.isfinite(x).all():
        raise ValueError('STATE_CONTRACT_MISMATCH')
    length = arclength(x)
    if length <= 0:
        raise ValueError('DEGENERATE_STATE')
    core = contract.core0 * (contract.reference_length / length) ** (.5 * contract.feedback_alpha)
    physical = velocity_from_cores(x, contract.gamma, np.full(len(x), core), contract.require_native)
    mesh = tangential_redistribution(x, contract.mesh_rate, contract.mesh_method)
    pr, mr = np.linalg.norm(physical), np.linalg.norm(mesh)
    if contract.mesh_cap > 0 and mr > contract.mesh_cap * max(pr, 1e-15):
        mesh *= contract.mesh_cap * max(pr, 1e-15) / mr
    return physical + mesh


def local_quality(x, contract):
    ds = segment_lengths(x)
    return {'ds_cv': float(ds.std() / max(ds.mean(), 1e-15)),
            'gap_over_ds': float(min_nonlocal_vertex_distance(x, contract.contact_skip) / max(ds.mean(), 1e-15))}


def integrate(x0, period, steps, contract, *, samples=16):
    """Fixed-step RK4; input perturbations cannot alter volume, dt or guard cadence."""
    if period <= 0 or steps < 1:
        raise ValueError('INVALID_TIME_GRID')
    x = np.asarray(x0, float).copy()
    dt = float(period) / int(steps)
    frames, times = [], []
    worst_cv, worst_gap = 0., float('inf')
    stride = max(1, int(steps) // max(1, int(samples)))
    f = lambda z: flow_rhs(z, contract)
    for k in range(int(steps) + 1):
        if k % contract.guard_stride == 0 or k == steps:
            quality = local_quality(x, contract)
            worst_cv = max(worst_cv, quality['ds_cv'])
            worst_gap = min(worst_gap, quality['gap_over_ds'])
            if worst_cv > contract.max_ds_cv or worst_gap < contract.min_gap_over_ds:
                raise RuntimeError('PHASE_B_GEOMETRY_GUARD_FAILED')
        if k % stride == 0 or k == steps:
            frames.append(x.copy()); times.append(k * dt)
        if k == steps:
            break
        k1 = f(x); k2 = f(x + .5*dt*k1); k3 = f(x + .5*dt*k2); k4 = f(x + dt*k3)
        x += dt * (k1 + 2*k2 + 2*k3 + k4) / 6
        if not np.isfinite(x).all():
            raise FloatingPointError('NONFINITE_FLOW')
    return {'final': x, 'x': np.asarray(frames), 't': np.asarray(times),
            'dt': dt, 'steps': int(steps), 'contract_sha256': contract.sha256,
            'worst_ds_cv': worst_cv, 'minimum_gap_over_ds': worst_gap,
            'return_quality': local_quality(x, contract)}


def central_jacobian(mapping, x, epsilon):
    x = np.asarray(x, float)
    if not np.isfinite(epsilon) or epsilon <= 0:
        raise ValueError('INVALID_FD_EPSILON')
    matrix = np.empty((x.size, x.size))
    for j in range(x.size):
        delta = np.zeros(x.size); delta[j] = epsilon; delta = delta.reshape(x.shape)
        matrix[:, j] = ((mapping(x + delta) - mapping(x - delta)) / (2 * epsilon)).ravel()
    return matrix


def symmetry_basis(x, velocity, rank_tol=1e-9):
    """Translations, rotations, time flow; redundant generators removed by SVD.

    Scaling and continuous re-indexing are NOT assumed symmetries of this model.
    At a relative equilibrium time flow can be dependent on spatial generators.
    """
    centered = x - np.mean(x, axis=0)
    cols = [np.broadcast_to(e, x.shape).ravel() for e in np.eye(3)]
    cols += [np.cross(np.broadcast_to(e, x.shape), centered).ravel() for e in np.eye(3)]
    cols += [np.asarray(velocity).ravel()]
    a = np.stack(cols, axis=1)
    norms = np.linalg.norm(a, axis=0)
    a = a[:, norms > 1e-14] / norms[norms > 1e-14]
    u, s, _ = np.linalg.svd(a, full_matrices=False)
    return u[:, s > rank_tol * s[0]]


def quotient_diagnostics(matrix, basis):
    complement = null_space(basis.T)
    mq = matrix @ basis
    leakage = np.linalg.norm(mq - basis @ (basis.T @ mq)) / max(np.linalg.norm(mq), 1e-30)
    reduced = complement.T @ matrix @ complement
    values, vectors = np.linalg.eig(reduced)
    residual = np.linalg.norm(reduced @ vectors - vectors * values) / max(np.linalg.norm(reduced), 1e-30)
    return {'symmetry_rank': basis.shape[1], 'quotient_dimension': reduced.shape[0],
            'symmetry_leakage': float(leakage), 'eigen_residual': float(residual),
            'spectral_radius': float(np.max(np.abs(values))),
            'eigenvector_condition': float(np.linalg.cond(vectors)),
            'multipliers': [[float(z.real), float(z.imag)] for z in values]}


def refine_full_state(x0, period, steps, contract, protocol):
    """Bounded full 3N shooting plus period and Euclidean return action.

    Seven phase conditions remove continuous gauge freedom (or the actual SVD
    rank at a relative equilibrium). The cyclic permutation remains fixed.
    A failed solve never becomes an RPO merely because the optimizer stopped.
    """
    x0 = np.asarray(x0, float)
    minimum = float(protocol['minimum_period'])
    if period < minimum:
        raise ValueError('RETURN_BEFORE_MINIMUM_PERIOD')
    baseline = integrate(x0, period, steps, contract)
    action = ReturnAction.fit(baseline['final'], x0)
    rot0 = Rotation.from_matrix(action.rotation).as_rotvec()
    phase = symmetry_basis(x0, flow_rhs(x0, contract))
    initial = np.r_[x0.ravel(), period, rot0, action.translation]
    radius = float(protocol['max_state_correction'])
    lower = np.r_[x0.ravel()-radius, max(minimum, period*.8), rot0-.5, np.asarray(action.translation)-1.]
    upper = np.r_[x0.ravel()+radius, period*1.2, rot0+.5, np.asarray(action.translation)+1.]

    def decode(z):
        act = ReturnAction(action.shift, tuple(map(tuple, Rotation.from_rotvec(z[-6:-3]).as_matrix())), tuple(z[-3:]))
        return z[:-7].reshape(x0.shape), float(z[-7]), act

    def residual(z):
        x, t, act = decode(z)
        end = integrate(x, t, steps, contract)['final']
        return np.r_[(act.apply(end)-x).ravel(), phase.T @ (x-x0).ravel()]

    fit = least_squares(residual, initial, bounds=(lower, upper),
                        max_nfev=int(protocol['shooting_max_nfev']),
                        ftol=1e-10, xtol=1e-10, gtol=1e-10)
    x, t, act = decode(fit.x)
    rms = float(np.linalg.norm(residual(fit.x)[:x.size]) / math.sqrt(len(x)))
    return x, t, act, {'optimizer_success': bool(fit.success), 'nfev': fit.nfev,
                       'return_rms': rms, 'full_state_dimension': x.size,
                       'status': 'RPO_RESIDUAL_PASSED' if rms <= protocol['rpo_rms_max'] else 'FAILED_RPO_RESIDUAL'}


def floquet_certificate(x, period, steps, contract, protocol, action=None, *, method='dense'):
    report = {'format': 'SST-FULLSTATE-FLOQUET-1', 'physics_scope': 'regularized filament / finite-core surrogate only',
              'physics_verdict': 'NOT_ESTABLISHED', 'dynamics_contract': asdict(contract),
              'dynamics_contract_sha256': contract.sha256, 'full_state_dimension': np.size(x),
              'initial_state_sha256': geom_sha(x),
              'period': float(period), 'steps': int(steps), 'method': method}
    if period < float(protocol['minimum_period']):
        return {**report, 'status': 'BLOCKED_EARLY_RETURN'}
    base = integrate(x, period, steps, contract)
    action = action or ReturnAction.fit(base['final'], x)
    closure = float(np.linalg.norm(action.apply(base['final'])-x) / math.sqrt(len(x)))
    report.update(return_rms=closure, return_action=asdict(action), return_quality=base['return_quality'])
    if closure > float(protocol['rpo_rms_max']):
        return {**report, 'status': 'BLOCKED_NO_ACCURATE_RPO'}
    if base['return_quality']['ds_cv'] > protocol['return_ds_cv_max'] or base['return_quality']['gap_over_ds'] < protocol['return_gap_over_ds_min']:
        return {**report, 'status': 'BLOCKED_RETURN_QUALITY'}
    mapping = lambda z: action.apply(integrate(z, period, steps, contract, samples=1)['final'])
    epsilons = [float(e) for e in protocol['fd_epsilons']]
    if len(epsilons) < 2 or any(e <= 0 for e in epsilons):
        raise ValueError('FD_LADDER_REQUIRED')
    basis = symmetry_basis(x, flow_rhs(x, contract))
    if method == 'arnoldi':
        # Partial spectrum: never a stability certificate for the unseen complement.
        z = null_space(basis.T)
        eps = epsilons[-1]
        def jvp(v):
            norm = np.linalg.norm(v)
            if norm == 0: return np.zeros_like(v)
            delta = (z @ (v/norm)).reshape(x.shape) * eps
            return z.T @ ((mapping(x+delta)-mapping(x-delta)).ravel()/(2*eps)) * norm
        operator = LinearOperator((z.shape[1], z.shape[1]), matvec=jvp, dtype=float)
        k = min(int(protocol['arnoldi_k']), z.shape[1]-2)
        try:
            values, vectors = eigs(operator, k=k, which='LM', tol=protocol['arnoldi_tol'],
                                    maxiter=protocol['arnoldi_maxiter'], v0=np.ones(z.shape[1]))
        except ArpackNoConvergence:
            return {**report, 'status': 'FAILED_ARNOLDI_CONVERGENCE'}
        residuals = []
        for value, vector in zip(values, vectors.T):
            jv = jvp(vector.real) + 1j*jvp(vector.imag)
            residuals.append(float(np.linalg.norm(jv-value*vector)/max(1.,abs(value))))
        return {**report, 'status': 'PARTIAL_SPECTRUM_NOT_CERTIFIED',
                'ritz_multipliers': [[float(v.real),float(v.imag)] for v in values],
                'ritz_residuals': residuals, 'unseen_spectrum_unbounded': True,
                'symmetry_removal_unverified': True}
    if method != 'dense':
        raise ValueError('UNKNOWN_FLOQUET_METHOD')
    if len(x) > int(protocol['dense_max_n']):
        return {**report, 'status': 'BLOCKED_DENSE_SIZE_USE_PARTIAL_ARNOLDI'}
    matrices = [central_jacobian(mapping, x, eps) for eps in epsilons]
    differences = [float(np.linalg.norm(a-b, 2)) for a,b in zip(matrices, matrices[1:])]
    matrix = matrices[-1]
    quotient = quotient_diagnostics(matrix, basis)
    fd_relative = max(differences) / max(np.linalg.norm(matrix,2),1e-30)
    velocity = flow_rhs(x, contract).ravel()
    neutral = float(np.linalg.norm(matrix@velocity-velocity) / max(np.linalg.norm(velocity),1e-30))
    tangent = tangents(x).ravel()
    gauge = float(np.linalg.norm(matrix@tangent-tangent)/max(np.linalg.norm(tangent),1e-30))
    okay = (fd_relative <= protocol['fd_relative_max'] and quotient['symmetry_leakage'] <= protocol['symmetry_leakage_max']
            and neutral <= protocol['time_neutral_residual_max'] and quotient['eigen_residual'] <= protocol['eigen_residual_max'])
    # Sensitivity indicator only: FD differences are NOT rigorous operator-error bounds.
    sensitivity = quotient['eigenvector_condition'] * max(differences)
    return {**report, **quotient, 'status': 'NUMERICALLY_VALIDATED_AT_DISCRETIZATION' if okay else 'FAILED_NUMERICAL_CERTIFICATION',
            'fd_epsilons': epsilons, 'fd_matrix_differences_2norm': differences,
            'fd_relative_difference': float(fd_relative), 'time_neutral_residual': neutral,
            'reparametrization_residual_not_removed': gauge,
            'spectral_sensitivity_indicator_not_bound': float(sensitivity),
            'stability_verdict': 'MULTI_LADDER_VALIDATION_REQUIRED',
            'rigorous_error_bounds': False, 'all_assumed_continuous_symmetries_checked': bool(okay)}


def intervention_panel(x, period, steps, contract, protocol, *, baseline_certificate):
    """Paired prospective intervention; the only changed field is feedback_alpha.

    A numerical intervention changes this surrogate, not nature. Sham comparison
    and primary outcome are fixed before results. Causal wording remains disabled
    until replicated and converged across the entire preregistered ladder.
    """
    if baseline_certificate.get('dynamics_contract_sha256') != contract.sha256:
        raise ValueError('INTERVENTION_BASELINE_CONTRACT_MISMATCH')
    if baseline_certificate.get('initial_state_sha256') != geom_sha(x):
        raise ValueError('INTERVENTION_BASELINE_STATE_MISMATCH')
    if baseline_certificate.get('status') != 'NUMERICALLY_VALIDATED_AT_DISCRETIZATION':
        return {'status': 'BLOCKED_NO_CERTIFIED_BASELINE', 'causal_language_allowed': False, 'arms': []}
    if float(baseline_certificate.get('period',-1)) != float(period) or baseline_certificate.get('steps') != steps:
        raise ValueError('INTERVENTION_TIME_GRID_MISMATCH')
    if contract.feedback_alpha != 1.0:
        raise ValueError('INTERVENTION_REQUIRES_NATIVE_BASELINE_ALPHA_ONE')
    action = ReturnAction(**baseline_certificate['return_action'])
    outcomes, final = [], {}
    for name, alpha in [('baseline',1.), ('sham',1.), ('half_feedback',.5), ('fixed_core_ablation',0.)]:
        arm = replace(contract, feedback_alpha=alpha)
        try:
            result = integrate(x, period, steps, arm)
            endpoint = result['final']; final[name] = endpoint
            fixed_rms = float(np.linalg.norm(action.apply(endpoint)-x)/math.sqrt(len(x)))
            shape_rms = float(align_cyclic(endpoint,x,1)[1])
            outcomes.append({'arm':name,'alpha':alpha,'status':'COMPLETED',
                             'fixed_group_return_rms':fixed_rms,'shape_return_rms':shape_rms,
                             'contract_sha256':arm.sha256, 'return_quality':result['return_quality']})
        except (ValueError, RuntimeError, FloatingPointError) as exc:
            outcomes.append({'arm':name,'alpha':alpha,'status':'FAILED_NUMERICS','error':str(exc)})
    complete = len(final)==4
    sham_error = float(np.max(np.abs(final['baseline']-final['sham']))) if 'sham' in final and 'baseline' in final else None
    okay = complete and sham_error <= protocol['sham_max_abs_error']
    if okay:
        baseline = outcomes[0]['fixed_group_return_rms']
        for row in outcomes:
            row['paired_primary_effect'] = row['fixed_group_return_rms']-baseline
    return {'status':'PAIRED_MODEL_INTERVENTION_COMPLETED' if okay else 'FAILED_INTERVENTION_CONTROLS',
            'primary_outcome':'fixed_group_return_rms_minus_matched_baseline',
            'arms':outcomes, 'sham_max_abs_error':sham_error, 'causal_language_allowed':False,
            'interpretation':'Model intervention only; replicated converged ladders required; no physical SST confirmation.'}


def run_ladders(x, period, cfg, protocol, *, refine=False):
    """No cherry-picking: enumerate the complete N x dt x core x mesh design.

    Each cell has its own fixed reference volume and group action. A certificate
    is per discretization; this runner does NOT equate different discretizations.
    """
    from itertools import product
    cells = []
    for n, dt_multiplier, core, mesh in product(protocol['resolution_ladder'],protocol['dt_multipliers'],
                                               protocol['core_ladder'],protocol['mesh_rate_ladder']):
        y = resample_closed(x,int(n))  # do not renormalize each resolution
        contract = FlowContract(int(n), arclength(y), gamma=float(cfg.get('gamma',1)), core0=core,
                                mesh_rate=mesh, mesh_cap=float(cfg.get('mesh_max_relative_rms',1)),
                                require_native=bool(cfg.get('require_native',True)))
        dt_max = float(cfg['dt_factor'])*dt_multiplier*float(min(segment_lengths(y)))**2/max(abs(contract.gamma),1e-15)
        steps = max(8, math.ceil(period/dt_max))
        cell = {'n':n,'dt_multiplier':dt_multiplier,'core':core,'mesh_rate':mesh,'steps':steps}
        try:
            if steps > int(cfg['max_steps']): raise RuntimeError('MAX_STEPS_EXCEEDED')
            if refine:
                y, t, action, fit = refine_full_state(y,period,steps,contract,protocol)
                cell['shooting']=fit
            else:
                t, action = period, None
            certificate = floquet_certificate(y,t,steps,contract,protocol,action)
            cell['floquet']=certificate
            cell['interventions']=intervention_panel(y,t,steps,contract,protocol,baseline_certificate=certificate)
        except (ValueError,RuntimeError,FloatingPointError,np.linalg.LinAlgError) as exc:
            cell['status']='FAILED_CELL'; cell['error']=str(exc)
        cells.append(cell)
    all_ok = all(c.get('floquet',{}).get('status')=='NUMERICALLY_VALIDATED_AT_DISCRETIZATION' for c in cells)
    return {'format':'SST-PHASE-B-LADDERS-1','cells':cells,'all_cells_numerically_validated':all_ok,
            'status':'CROSS_LADDER_COMPARISON_REQUIRED' if all_ok else 'INDETERMINATE_INCOMPLETE_LADDERS',
            'physics_verdict':'NOT_ESTABLISHED','causal_language_allowed':False}
