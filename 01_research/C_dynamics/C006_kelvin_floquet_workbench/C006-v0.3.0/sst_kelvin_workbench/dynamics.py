"""Blind coupled-Kelvin/Floquet eigenmode clock for a counter-rotating vortex pair.

The solver never imports or stores the fine-structure constant.  It linearises the
same regularised Biot--Savart two-filament ODE used by the native backend, projects
that temporal Jacobian onto a pre-registered four-dimensional Kelvin subspace
(m=1, two circular helicities, common/differential channel parity), and extracts a
counter-propagating eigenmode doublet.

The internal clock is built from the selected eigenfrequencies themselves:

    omega_clock = (|omega_+| + |omega_-|)/2,
    T_clock     = 2*pi/omega_clock,
    h_F         = arg(mu_+ * mu_-)/(2*pi),
    mu_j        = exp(lambda_j T_clock).

No relation dt=ds/U and no alpha-derived scale enters this construction.

A genuine Floquet interpretation still requires the base pair to be a relative
equilibrium or a periodic orbit.  The best rigid translation+rotation residual is
therefore reported and used as a hard scientific gate.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from typing import Any
import numpy as np

from .backend import load_backend
from .geometry import bishop_frame, make_counter_channels


def turn_wrap(x: float) -> float:
    y = (float(x) + 0.5) % 1.0 - 0.5
    if y <= -0.5:
        y += 1.0
    return y


def pair_rhs(plus: np.ndarray, minus: np.ndarray, gamma_plus: float, gamma_minus: float,
             eps: float, *, backend: Any) -> np.ndarray:
    """Regularised two-filament Biot--Savart ODE, shape (2N,3)."""
    p = np.ascontiguousarray(plus, dtype=float)
    m = np.ascontiguousarray(minus, dtype=float)
    if hasattr(backend, "pair_rhs"):
        return np.asarray(backend.pair_rhs(p, m, gamma_plus, gamma_minus, eps), dtype=float)
    vp = (np.asarray(backend.induced_velocity(p, p, gamma_plus, eps), dtype=float)
          + np.asarray(backend.induced_velocity(p, m, gamma_minus, eps), dtype=float))
    vm = (np.asarray(backend.induced_velocity(m, m, gamma_minus, eps), dtype=float)
          + np.asarray(backend.induced_velocity(m, p, gamma_plus, eps), dtype=float))
    return np.vstack((vp, vm))


def _omega_cross_matrix(r: np.ndarray) -> np.ndarray:
    """Matrix C(r) such that C(r) @ Omega = Omega x r."""
    x, y, z = map(float, r)
    return np.array([[0.0, z, -y], [-z, 0.0, x], [y, -x, 0.0]], dtype=float)


def fit_rigid_velocity(points: np.ndarray, velocity: np.ndarray) -> dict[str, Any]:
    """Least-squares fit u = V + Omega x (x-xc)."""
    x = np.asarray(points, dtype=float)
    v = np.asarray(velocity, dtype=float)
    xc = np.mean(x, axis=0)
    r = x - xc
    A = np.zeros((3 * len(x), 6), dtype=float)
    for i, ri in enumerate(r):
        A[3*i:3*i+3, :3] = np.eye(3)
        A[3*i:3*i+3, 3:] = _omega_cross_matrix(ri)
    sol, *_ = np.linalg.lstsq(A, v.reshape(-1), rcond=None)
    pred = (A @ sol).reshape((-1, 3))
    res = v - pred
    speed_rms = float(np.sqrt(np.mean(np.einsum("ij,ij->i", v, v))))
    residual_rms = float(np.sqrt(np.mean(np.einsum("ij,ij->i", res, res))))
    return {
        "translation": np.asarray(sol[:3], dtype=float),
        "omega": np.asarray(sol[3:], dtype=float),
        "speed_rms": speed_rms,
        "residual_rms": residual_rms,
        "relative_equilibrium_residual": residual_rms / max(speed_rms, 1e-30),
    }


def rotate_normal_basis(normal: np.ndarray, binormal: np.ndarray, phase: float) -> tuple[np.ndarray, np.ndarray]:
    """Constant gauge rotation of a fixed physical channel frame."""
    c, s = math.cos(float(phase)), math.sin(float(phase))
    n = c*np.asarray(normal, dtype=float) + s*np.asarray(binormal, dtype=float)
    b = -s*np.asarray(normal, dtype=float) + c*np.asarray(binormal, dtype=float)
    return n, b


def embed_transverse(q: np.ndarray, normal: np.ndarray, binormal: np.ndarray) -> np.ndarray:
    """Map 4N transverse coordinates to Cartesian displacements of two N-point channels."""
    q = np.asarray(q)
    n = np.asarray(normal, dtype=float); b = np.asarray(binormal, dtype=float)
    N = len(n)
    if q.shape != (4*N,):
        raise ValueError(f"q must have shape ({4*N},)")
    out = np.empty((2*N, 3), dtype=np.result_type(q.dtype, float))
    for ch in range(2):
        block = q[ch*2*N:(ch+1)*2*N]
        out[ch*N:(ch+1)*N] = block[0::2, None]*n + block[1::2, None]*b
    return out


def project_transverse(v: np.ndarray, normal: np.ndarray, binormal: np.ndarray) -> np.ndarray:
    """Project Cartesian two-channel vectors onto 4N transverse coordinates."""
    v = np.asarray(v)
    n = np.asarray(normal, dtype=float); b = np.asarray(binormal, dtype=float)
    N = len(n)
    if v.shape != (2*N, 3):
        raise ValueError(f"v must have shape ({2*N},3)")
    out = np.empty(4*N, dtype=np.result_type(v.dtype, float))
    for ch in range(2):
        vv = v[ch*N:(ch+1)*N]
        block = out[ch*2*N:(ch+1)*2*N]
        block[0::2] = np.einsum("ij,ij->i", vv, n)
        block[1::2] = np.einsum("ij,ij->i", vv, b)
    return out


def _station_phase(centerline: np.ndarray, m: int = 1) -> np.ndarray:
    c = np.asarray(centerline, dtype=float)
    seg = np.linalg.norm(np.roll(c, -1, axis=0) - c, axis=1)
    s = np.concatenate(([0.0], np.cumsum(seg[:-1])))
    return 2.0 * math.pi * int(m) * s / float(np.sum(seg))


def kelvin_template(centerline: np.ndarray, *, sector: str, helicity: int, m: int = 1) -> np.ndarray:
    """Circular m-th Kelvin template in transverse coordinate space.

    The four pre-registered basis states are common/differential channel parity
    crossed with helicity +/-1.  They are independent of alpha.
    """
    if sector not in {"common", "differential"}:
        raise ValueError("sector must be common or differential")
    if helicity not in {-1, 1}:
        raise ValueError("helicity must be +/-1")
    N = len(centerline)
    z = np.exp(1j * _station_phase(centerline, m=m))
    one = np.empty(2*N, dtype=complex)
    one[0::2] = z
    one[1::2] = 1j * helicity * z
    out = np.empty(4*N, dtype=complex)
    out[:2*N] = one
    out[2*N:] = one if sector == "common" else -one
    return out / np.linalg.norm(out)


def _transverse_action(q_real: np.ndarray, *, x0: np.ndarray, N: int,
                       normal: np.ndarray, binormal: np.ndarray, rigid_omega: np.ndarray,
                       gamma_plus: float, gamma_minus: float, eps: float, h: float,
                       omega_gamma: float, backend: Any) -> np.ndarray:
    """Apply the dimensionless co-rigid temporal Jacobian to one real transverse vector."""
    dx = embed_transverse(np.asarray(q_real, dtype=float), normal, binormal)
    xp = x0 + h*dx
    xm = x0 - h*dx
    vp = pair_rhs(xp[:N], xp[N:], gamma_plus, gamma_minus, eps, backend=backend)
    vm = pair_rhs(xm[:N], xm[N:], gamma_plus, gamma_minus, eps, backend=backend)
    dv = (vp - vm)/(2.0*h)
    corot = np.cross(np.repeat(np.asarray(rigid_omega)[None, :], 2*N, axis=0), dx)
    return project_transverse(dv - corot, normal, binormal) / omega_gamma


def projected_kelvin_analysis(centerline: np.ndarray, *, D: float,
                              offset_over_D: float = 0.5, eps_over_D: float = 0.05,
                              fd_step_over_D: float = 2e-5,
                              gamma_plus: float = 1.0, gamma_minus: float = -1.0,
                              channel_phase: float = 0.0, basis_phase: float = 0.0,
                              mode_m: int = 1,
                              force_python: bool = False, skip_build: bool = False,
                              force_build: bool = False, build_verbose: bool = False) -> dict[str, Any]:
    """Project the true temporal Biot--Savart Jacobian onto the m=1 Kelvin subspace."""
    c = np.ascontiguousarray(centerline, dtype=float)
    if D <= 0 or eps_over_D <= 0 or fd_step_over_D <= 0 or offset_over_D <= 0:
        raise ValueError("D, offset, eps and finite-difference step must be positive")
    plus, minus, tangent, normal_phys = make_counter_channels(c, offset_over_D*D, phase=channel_phase)
    _, normal_phys, binormal_phys = bishop_frame(c, phase=channel_phase)
    normal, binormal = rotate_normal_basis(normal_phys, binormal_phys, basis_phase)
    backend, backend_name = load_backend(force_python=force_python, skip_build=skip_build,
                                         force_build=force_build, build_verbose=build_verbose)
    eps = eps_over_D*D
    h = fd_step_over_D*D
    x0 = np.vstack((plus, minus))
    v0 = pair_rhs(plus, minus, gamma_plus, gamma_minus, eps, backend=backend)
    rigid = fit_rigid_velocity(x0, v0)
    gscale = 0.5*(abs(gamma_plus)+abs(gamma_minus))
    omega_gamma = gscale/(4.0*math.pi*D*D)
    if omega_gamma <= 0:
        raise ValueError("nonzero circulation scale required")

    labels = ["h+_common", "h+_differential", "h-_common", "h-_differential"]
    Q = np.column_stack([
        kelvin_template(c, sector="common", helicity=1, m=mode_m),
        kelvin_template(c, sector="differential", helicity=1, m=mode_m),
        kelvin_template(c, sector="common", helicity=-1, m=mode_m),
        kelvin_template(c, sector="differential", helicity=-1, m=mode_m),
    ])
    gram = np.conjugate(Q).T @ Q
    Y = np.zeros_like(Q, dtype=complex)
    for j in range(Q.shape[1]):
        yr = _transverse_action(Q[:, j].real, x0=x0, N=len(c), normal=normal, binormal=binormal,
                                rigid_omega=rigid["omega"], gamma_plus=gamma_plus,
                                gamma_minus=gamma_minus, eps=eps, h=h,
                                omega_gamma=omega_gamma, backend=backend)
        yi = _transverse_action(Q[:, j].imag, x0=x0, N=len(c), normal=normal, binormal=binormal,
                                rigid_omega=rigid["omega"], gamma_plus=gamma_plus,
                                gamma_minus=gamma_minus, eps=eps, h=h,
                                omega_gamma=omega_gamma, backend=backend)
        Y[:, j] = yr + 1j*yi
    G = np.conjugate(Q).T @ Y
    vals, vecs = np.linalg.eig(G)
    pos = [i for i,z in enumerate(vals) if z.imag > 1e-8]
    neg = [i for i,z in enumerate(vals) if z.imag < -1e-8]
    if not pos or not neg:
        raise ValueError("projected Kelvin subspace lacks a counter-propagating oscillatory pair")
    quality = lambda z: abs(float(z.real))/max(abs(float(z.imag)), 1e-30)
    ip = min(pos, key=lambda i: quality(vals[i]))
    im = min(neg, key=lambda i: quality(vals[i]))
    lp, lm = complex(vals[ip]), complex(vals[im])
    wp, wm = float(lp.imag), float(-lm.imag)
    wclock = 0.5*(wp+wm)
    Tclock = 2.0*math.pi/wclock
    # Counter-propagating doublet: product phase is the signed frequency asymmetry.
    phase_algebraic = turn_wrap((wp-wm)/wclock)
    phase_multiplier = turn_wrap(float(np.angle(np.exp(1j*(lp.imag+lm.imag)*Tclock))/(2.0*math.pi)))
    coeff_p = np.abs(vecs[:, ip])**2; coeff_p /= np.sum(coeff_p)
    coeff_m = np.abs(vecs[:, im])**2; coeff_m /= np.sum(coeff_m)
    return {
        "backend": backend_name,
        "omega_gamma": float(omega_gamma),
        "rigid": rigid,
        "gram_error_fro": float(np.linalg.norm(gram-np.eye(4))),
        "generator": G,
        "generator_fro": float(np.linalg.norm(G)),
        "eigenvalues": vals,
        "eigenvectors": vecs,
        "basis_labels": labels,
        "selected_positive_index": int(ip),
        "selected_negative_index": int(im),
        "lambda_positive_hat": lp,
        "lambda_negative_hat": lm,
        "positive_quality_re_over_im": float(quality(lp)),
        "negative_quality_re_over_im": float(quality(lm)),
        "positive_basis_weights": {labels[k]: float(coeff_p[k]) for k in range(4)},
        "negative_basis_weights": {labels[k]: float(coeff_m[k]) for k in range(4)},
        "omega_positive_hat": wp,
        "omega_negative_abs_hat": wm,
        "eigen_clock_omega_hat": float(wclock),
        "eigen_clock_period_hat": float(Tclock),
        "mu_positive_log_abs": float(lp.real*Tclock),
        "mu_negative_log_abs": float(lm.real*Tclock),
        "floquet_phase_signed_turns": float(phase_multiplier),
        "floquet_phase_algebraic_turns": float(phase_algebraic),
        "floquet_phase_scalar_defect_turns": float(-abs(phase_multiplier)),
        "phase_internal_consistency_turns": float(abs(turn_wrap(phase_multiplier-phase_algebraic))),
    }


@dataclass
class DynamicBlindResult:
    n: int
    D: float
    offset_over_D: float
    eps_over_D: float
    fd_step_over_D: float
    gamma_plus: float
    gamma_minus: float
    channel_phase_rad: float
    basis_phase_rad: float
    backend: str
    omega_gamma: float
    relative_equilibrium_residual: float
    rigid_speed_rms_dimless: float
    rigid_residual_rms_dimless: float
    gram_error_fro: float
    generator_fro: float
    mode_m: int
    lambda_positive_real_hat: float
    lambda_positive_imag_hat: float
    lambda_negative_real_hat: float
    lambda_negative_imag_hat: float
    positive_quality_re_over_im: float
    negative_quality_re_over_im: float
    omega_positive_hat: float
    omega_negative_abs_hat: float
    eigen_clock_omega_hat: float
    eigen_clock_period_hat: float
    mu_positive_log_abs: float
    mu_negative_log_abs: float
    floquet_phase_signed_turns: float
    floquet_phase_scalar_defect_turns: float
    phase_internal_consistency_turns: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_dynamic_blind(centerline: np.ndarray, *, D: float,
                          offset_over_D: float = 0.5, eps_over_D: float = 0.05,
                          fd_step_over_D: float = 2e-5,
                          gamma_plus: float = 1.0, gamma_minus: float = -1.0,
                          channel_phase: float = 0.0, basis_phase: float = 0.0,
                          mode_m: int = 1,
                          force_python: bool = False, skip_build: bool = False,
                          force_build: bool = False, build_verbose: bool = False) -> DynamicBlindResult:
    a = projected_kelvin_analysis(
        centerline, D=D, offset_over_D=offset_over_D, eps_over_D=eps_over_D,
        fd_step_over_D=fd_step_over_D, gamma_plus=gamma_plus, gamma_minus=gamma_minus,
        channel_phase=channel_phase, basis_phase=basis_phase, mode_m=mode_m,
        force_python=force_python, skip_build=skip_build, force_build=force_build,
        build_verbose=build_verbose)
    rigid = a["rigid"]
    speed_scale = a["omega_gamma"]*D
    lp, lm = a["lambda_positive_hat"], a["lambda_negative_hat"]
    return DynamicBlindResult(
        n=len(centerline), D=float(D), offset_over_D=float(offset_over_D), eps_over_D=float(eps_over_D),
        fd_step_over_D=float(fd_step_over_D), gamma_plus=float(gamma_plus), gamma_minus=float(gamma_minus),
        channel_phase_rad=float(channel_phase), basis_phase_rad=float(basis_phase), backend=str(a["backend"]),
        omega_gamma=float(a["omega_gamma"]),
        relative_equilibrium_residual=float(rigid["relative_equilibrium_residual"]),
        rigid_speed_rms_dimless=float(rigid["speed_rms"]/max(speed_scale,1e-30)),
        rigid_residual_rms_dimless=float(rigid["residual_rms"]/max(speed_scale,1e-30)),
        gram_error_fro=float(a["gram_error_fro"]), generator_fro=float(a["generator_fro"]),
        mode_m=int(mode_m),
        lambda_positive_real_hat=float(lp.real), lambda_positive_imag_hat=float(lp.imag),
        lambda_negative_real_hat=float(lm.real), lambda_negative_imag_hat=float(lm.imag),
        positive_quality_re_over_im=float(a["positive_quality_re_over_im"]),
        negative_quality_re_over_im=float(a["negative_quality_re_over_im"]),
        omega_positive_hat=float(a["omega_positive_hat"]), omega_negative_abs_hat=float(a["omega_negative_abs_hat"]),
        eigen_clock_omega_hat=float(a["eigen_clock_omega_hat"]), eigen_clock_period_hat=float(a["eigen_clock_period_hat"]),
        mu_positive_log_abs=float(a["mu_positive_log_abs"]), mu_negative_log_abs=float(a["mu_negative_log_abs"]),
        floquet_phase_signed_turns=float(a["floquet_phase_signed_turns"]),
        floquet_phase_scalar_defect_turns=float(a["floquet_phase_scalar_defect_turns"]),
        phase_internal_consistency_turns=float(a["phase_internal_consistency_turns"]),
    )


def projected_kelvin_analysis_fixed(centerline: np.ndarray, plus: np.ndarray, minus: np.ndarray,
                                    normal: np.ndarray, binormal: np.ndarray, *, D: float,
                                    eps_over_D: float = 0.05, fd_step_over_D: float = 2e-5,
                                    gamma_plus: float = 1.0, gamma_minus: float = -1.0,
                                    basis_phase: float = 0.0, mode_m: int = 1,
                                    force_python: bool = False, skip_build: bool = False) -> dict[str, Any]:
    """Same projected temporal analysis for already-defined physical channels.

    This is used for strict Euclidean-invariance tests: the physical channels and
    their transverse basis are rigidly transformed instead of being regenerated
    from a global-axis-dependent Bishop-frame seed.
    """
    c=np.ascontiguousarray(centerline,dtype=float); p=np.ascontiguousarray(plus,dtype=float); m=np.ascontiguousarray(minus,dtype=float)
    n,b=rotate_normal_basis(np.asarray(normal,dtype=float),np.asarray(binormal,dtype=float),basis_phase)
    backend,backend_name=load_backend(force_python=force_python,skip_build=skip_build)
    eps=eps_over_D*D; h=fd_step_over_D*D; x0=np.vstack((p,m))
    v0=pair_rhs(p,m,gamma_plus,gamma_minus,eps,backend=backend); rigid=fit_rigid_velocity(x0,v0)
    gscale=.5*(abs(gamma_plus)+abs(gamma_minus)); omega_gamma=gscale/(4*math.pi*D*D)
    labels=["h+_common","h+_differential","h-_common","h-_differential"]
    Q=np.column_stack([kelvin_template(c,sector="common",helicity=1,m=mode_m),kelvin_template(c,sector="differential",helicity=1,m=mode_m),kelvin_template(c,sector="common",helicity=-1,m=mode_m),kelvin_template(c,sector="differential",helicity=-1,m=mode_m)])
    gram=np.conjugate(Q).T@Q; Y=np.zeros_like(Q,dtype=complex)
    for j in range(4):
        yr=_transverse_action(Q[:,j].real,x0=x0,N=len(c),normal=n,binormal=b,rigid_omega=rigid["omega"],gamma_plus=gamma_plus,gamma_minus=gamma_minus,eps=eps,h=h,omega_gamma=omega_gamma,backend=backend)
        yi=_transverse_action(Q[:,j].imag,x0=x0,N=len(c),normal=n,binormal=b,rigid_omega=rigid["omega"],gamma_plus=gamma_plus,gamma_minus=gamma_minus,eps=eps,h=h,omega_gamma=omega_gamma,backend=backend)
        Y[:,j]=yr+1j*yi
    G=np.conjugate(Q).T@Y; vals,vecs=np.linalg.eig(G)
    pos=[i for i,z in enumerate(vals) if z.imag>1e-8]; neg=[i for i,z in enumerate(vals) if z.imag<-1e-8]
    quality=lambda z: abs(float(z.real))/max(abs(float(z.imag)),1e-30)
    ip=min(pos,key=lambda i:quality(vals[i])); im=min(neg,key=lambda i:quality(vals[i])); lp,lm=complex(vals[ip]),complex(vals[im])
    wp,wm=float(lp.imag),float(-lm.imag); wc=.5*(wp+wm); T=2*math.pi/wc
    phase=turn_wrap(float(np.angle(np.exp(1j*(lp.imag+lm.imag)*T))/(2*math.pi)))
    return {"backend":backend_name,"omega_gamma":float(omega_gamma),"rigid":rigid,"gram_error_fro":float(np.linalg.norm(gram-np.eye(4))),"generator":G,"eigenvalues":vals,"lambda_positive_hat":lp,"lambda_negative_hat":lm,"omega_positive_hat":wp,"omega_negative_abs_hat":wm,"positive_quality_re_over_im":float(quality(lp)),"negative_quality_re_over_im":float(quality(lm)),"eigen_clock_omega_hat":float(wc),"eigen_clock_period_hat":float(T),"floquet_phase_signed_turns":float(phase)}
