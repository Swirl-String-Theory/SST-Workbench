import math
import numpy as np
from .biotsavart import velocity
from .geometry import curve_length, resample_arclength, kabsch_align
from .bishop import bishop_frame
from .constants import GAMMA_STAR, CORE_RADIUS_STAR, T_CORE


def _rel(a, b, floor=1e-14):
    return abs(a-b)/max(abs(a), abs(b), floor)


def rk4_step(x, dt, require_native=False):
    f = lambda z: velocity(z, GAMMA_STAR, CORE_RADIUS_STAR, require_native=require_native)
    k1 = f(x)
    k2 = f(x + .5*dt*k1)
    k3 = f(x + .5*dt*k2)
    k4 = f(x + dt*k3)
    return x + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)


def helical_perturbation(x, mode, eps):
    _, e1, e2 = bishop_frame(x)
    ph = 2*np.pi*mode*np.arange(len(x))/len(x)
    return x + eps*(np.cos(ph)[:,None]*e1 + np.sin(ph)[:,None]*e2)


def mode_amplitude(base, pert, mode):
    pa = kabsch_align(pert, base)
    d = pa-base
    _, e1, e2 = bishop_frame(base)
    z = np.einsum('ij,ij->i',d,e1) + 1j*np.einsum('ij,ij->i',d,e2)
    ph = np.exp(-1j*2*np.pi*mode*np.arange(len(base))/len(base))
    return np.mean(z*ph)


def _fit_phase(times, amps):
    times = np.asarray(times); amps = np.asarray(amps)
    mag = np.abs(amps); mask = np.isfinite(mag) & (mag > 1e-12)
    if mask.sum() < 5:
        return float('nan'), float('nan'), float('nan')
    tt = times[mask]
    ph = np.unwrap(np.angle(amps[mask]))
    A = np.vstack([tt,np.ones_like(tt)]).T
    w,b = np.linalg.lstsq(A,ph,rcond=None)[0]
    pred = w*tt+b
    ssr = float(np.sum((ph-pred)**2))
    sst = float(np.sum((ph-ph.mean())**2))
    r2 = 1-ssr/max(sst,1e-30)
    growth = np.linalg.lstsq(A,np.log(np.maximum(mag[mask],1e-30)),rcond=None)[0][0]
    return float(w), float(growth), float(r2)


def projected_linear_mode(x_core, mode, cfg, eps_override=None):
    """Galerkin projection of the instantaneous linearized regularized
    Biot-Savart operator onto four Bishop/Fourier quadratures.

    This is a local linear-response operator. It is not a Floquet exponent unless
    the base curve is independently established as a stationary/relative-periodic
    solution of the same dynamics.
    """
    n = len(x_core)
    _, e1, e2 = bishop_frame(x_core)
    th = 2*np.pi*mode*np.arange(n)/n
    c = np.cos(th)[:,None]; s = np.sin(th)[:,None]
    basis = [c*e1, s*e1, c*e2, s*e2]
    eps = float(eps_override if eps_override is not None else cfg.get('linearization_eps_core', 0.01))
    req = bool(cfg.get('require_native', False))

    G = np.empty((4,4)); R = np.empty((4,4))
    for i in range(4):
        for j in range(4):
            G[i,j] = float(np.mean(np.sum(basis[i]*basis[j],axis=1)))
    condG = float(np.linalg.cond(G))

    for j,B in enumerate(basis):
        vp = velocity(x_core+eps*B, GAMMA_STAR, CORE_RADIUS_STAR, require_native=req)
        vm = velocity(x_core-eps*B, GAMMA_STAR, CORE_RADIUS_STAR, require_native=req)
        dV = (vp-vm)/(2*eps)
        dV = dV-dV.mean(axis=0)  # discard differential rigid translation
        for i in range(4):
            R[i,j] = float(np.mean(np.sum(basis[i]*dV,axis=1)))

    M = np.linalg.solve(G,R)
    eig = np.linalg.eigvals(M)
    k = int(np.argmax(np.abs(np.imag(eig))))
    lam = eig[k]
    return {
        'omega_linear_core': float(abs(np.imag(lam))),
        'growth_linear_core': float(np.real(lam)),
        'max_growth_core': float(np.max(np.real(eig))),
        'gram_condition': condG,
        'eps_core': eps,
        'linear_eigenvalues': [[float(z.real),float(z.imag)] for z in eig],
        'linear_matrix': M.tolist(),
    }


def run_mode(x_core, mode, cfg, dt_factor=1.0):
    n = len(x_core); L = curve_length(x_core); ds = L/n
    eps_lin = float(cfg.get('linearization_eps_core',0.01))
    lin = projected_linear_mode(x_core, mode, cfg, eps_override=eps_lin)
    lin_half = projected_linear_mode(x_core, mode, cfg, eps_override=0.5*eps_lin)
    lin_err = _rel(lin['omega_linear_core'], lin_half['omega_linear_core'])

    tf = float(cfg.get('t_final_core',.03))
    dt_raw = dt_factor*float(cfg.get('cfl',.25))*ds*ds
    min_steps = int(cfg.get('min_steps',48))
    nsteps = max(int(math.ceil(min_steps/max(dt_factor,1e-12))), int(math.ceil(tf/max(dt_raw,1e-10))))
    dt = tf/nsteps
    eps = float(cfg.get('perturbation_core',.03))
    re = int(cfg.get('reparam_every',2)); samp = max(1,int(cfg.get('sample_every',1)))
    req = bool(cfg.get('require_native',False))
    base = x_core.copy(); pert = helical_perturbation(base,mode,eps)
    ts = [0.0]; aa = [mode_amplitude(base,pert,mode)]
    for step in range(1,nsteps+1):
        base = rk4_step(base,dt,req); pert = rk4_step(pert,dt,req)
        if re > 0 and step % re == 0:
            base = resample_arclength(base,n); pert = resample_arclength(pert,n)
        if step % samp == 0 or step == nsteps:
            ts.append(step*dt); aa.append(mode_amplitude(base,pert,mode))
    w,g,r2 = _fit_phase(ts,aa)
    q = 2*np.pi*mode/L
    om = lin['omega_linear_core']
    return {
        'mode': int(mode), 'n_points': n, 'q_core': float(q),
        'omega_core': om, 'omega2_core': float(om**2),
        'growth_core': lin['growth_linear_core'],
        'max_growth_core': lin['max_growth_core'],
        'frequency_source': 'projected_linear_operator',
        'linearization_eps_rel_error': float(lin_err),
        'gram_condition': lin['gram_condition'],
        'track_omega_core': w, 'track_growth_core': g, 'phase_r2': r2,
        'n_steps': nsteps, 'dt_core': dt, 't_final_core': tf,
        'omega_rad_s': float(om/T_CORE),
        'frequency_hz': float(om/(2*np.pi*T_CORE)),
        'linear_eigenvalues': lin['linear_eigenvalues'],
        'linear_eigenvalues_half_eps': lin_half['linear_eigenvalues'],
        'linear_matrix': lin['linear_matrix'],
    }


def fit_dispersion(rows, cfg):
    max_lin_err = float(cfg.get('linearization_rel_tol',0.08))
    min_good = int(cfg.get('min_good_modes',4))
    good = [r for r in rows
            if np.isfinite(r['omega2_core']) and r['omega2_core'] > 0
            and np.isfinite(r.get('linearization_eps_rel_error',np.inf))
            and r['linearization_eps_rel_error'] <= max_lin_err]
    if len(good) < min_good:
        return {
            'n_good': len(good), 'n_required': min_good,
            'status': 'INSUFFICIENT', 'linearization_rel_tol': max_lin_err
        }

    q = np.array([r['q_core'] for r in good],float)
    y = np.array([r['omega2_core'] for r in good],float)

    X24 = np.column_stack([q*q,q**4])
    c24 = np.linalg.lstsq(X24,y,rcond=None)[0]
    p24 = X24@c24
    rmse24 = float(np.sqrt(np.mean((y-p24)**2)))
    scale = max(float(np.sqrt(np.mean(y*y))),1e-30)
    rel24 = rmse24/scale
    ssr = float(np.sum((y-p24)**2)); sst = float(np.sum((y-y.mean())**2))

    X2 = (q*q)[:,None]
    c2 = np.linalg.lstsq(X2,y,rcond=None)[0]
    p2 = X2@c2
    rmse2 = float(np.sqrt(np.mean((y-p2)**2)))
    rel2 = rmse2/scale
    gain = (rel2-rel24)/max(rel2,1e-30)

    return {
        'n_good': len(good), 'n_required': min_good, 'status': 'OK',
        'a2': float(c24[0]), 'a4': float(c24[1]),
        'rel_rmse': float(rel24), 'r2': 1-ssr/max(sst,1e-30),
        'q2_only_a2': float(c2[0]), 'q2_only_rel_rmse': float(rel2),
        'quartic_relative_improvement': float(gain),
        'linearization_rel_tol': max_lin_err,
        'good_modes': [int(r['mode']) for r in good],
    }
