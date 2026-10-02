from __future__ import annotations
import math
import numpy as np
from .geometry import frames

try:
    from native_ext import velocity_at_points, transverse_jacobian, writhe
except Exception as e:  # pragma: no cover
    velocity_at_points = transverse_jacobian = writhe = None
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


def require_native():
    if velocity_at_points is None:
        raise RuntimeError(f"native_ext unavailable: {_IMPORT_ERROR}. Run run_01_build_native.cmd")


def tube_helicity_xi(curve: np.ndarray, core: float, radial_nodes: int = 3, angles: int = 8) -> float:
    """Approximate H/Gamma^2 for an untwisted Gaussian finite-core tube.

    omega(r) = Gamma/(pi a^2) exp(-r^2/a^2) t.
    Velocity is the same regularized centerline Biot-Savart field used by dynamics.
    Integration is over r in [0,3a].  This is a finite-core diagnostic, not an
    identity H/Gamma^2 = Wr + Tw.
    """
    require_native()
    x = np.asarray(curve, dtype=np.float64)
    t, n, b, kappa = frames(x)
    seg = np.linalg.norm(np.roll(x, -1, axis=0) - x, axis=1)
    ds = 0.5 * (seg + np.roll(seg, 1))
    nodes, weights = np.polynomial.legendre.leggauss(radial_nodes)
    rmax = 3.0 * core
    rs = 0.5 * (nodes + 1.0) * rmax
    wr = 0.5 * rmax * weights
    thetas = 2.0 * math.pi * np.arange(angles) / angles
    dtheta = 2.0 * math.pi / angles

    pts = []
    omega = []
    dvol = []
    for i in range(len(x)):
        for r, rw in zip(rs, wr):
            amp = math.exp(-(r/core)**2) / (math.pi * core * core)
            for th in thetas:
                c, s = math.cos(th), math.sin(th)
                pts.append(x[i] + r * (c*n[i] + s*b[i]))
                omega.append(amp * t[i])
                jac = max(0.05, 1.0 - kappa[i] * r * c)
                dvol.append(ds[i] * r * rw * dtheta * jac)
    pts = np.ascontiguousarray(np.array(pts, dtype=np.float64))
    omega = np.array(omega, dtype=np.float64)
    dvol = np.array(dvol, dtype=np.float64)
    vel = np.asarray(velocity_at_points(x, pts, core, 1.0))
    H = np.sum(np.einsum("ij,ij->i", vel, omega) * dvol)
    return float(H)  # Gamma=1, so H/Gamma^2 == H numerically.


def build_operator(curve: np.ndarray, core: float, fd_eps: float) -> tuple[np.ndarray, dict]:
    require_native()
    _, n, b, _ = frames(curve)
    J = np.asarray(transverse_jacobian(curve, n, b, core, 1.0, fd_eps), dtype=np.float64)
    dim = J.shape[0]
    frob_rms = float(np.linalg.norm(J, ord="fro") / math.sqrt(dim))
    scale = max(frob_rms, 1e-12)
    Jh = J / scale
    rate_inf = float(np.max(np.sum(np.abs(Jh), axis=1)))
    return Jh, {"operator_rate_scale_Gamma_over_L2": scale, "normalized_inf_rate": rate_inf}


def initial_packet(npts: int, center: float, width: float, mode: int) -> np.ndarray:
    s = np.arange(npts, dtype=np.float64) / npts
    d = np.minimum(np.abs(s-center), 1.0-np.abs(s-center))
    env = np.exp(-0.5*(d/width)**2)
    a = env * np.cos(2.0*np.pi*mode*(s-center))
    a -= a.mean()
    b = np.zeros_like(a)
    u = np.concatenate([a,b])
    u /= max(np.linalg.norm(u), 1e-30)
    return u


def polarity(u: np.ndarray) -> float:
    n = len(u)//2
    z = u[:n] + 1j*u[n:]
    Z = np.fft.fft(z)
    f = np.fft.fftfreq(n)
    p = float(np.sum(np.abs(Z[f>0])**2))
    m = float(np.sum(np.abs(Z[f<0])**2))
    return (p-m)/max(p+m, 1e-30)


def _rk4_step(J: np.ndarray, u: np.ndarray, dt: float) -> np.ndarray:
    k1 = J @ u
    k2 = J @ (u + 0.5*dt*k1)
    k3 = J @ (u + 0.5*dt*k2)
    k4 = J @ (u + dt*k3)
    return u + (dt/6.0)*(k1 + 2*k2 + 2*k3 + k4)


def evolve_packet(J: np.ndarray, u0: np.ndarray, final_operator_time: float, output_steps: int, max_dt_rate: float, rate_inf: float) -> dict:
    u = u0.copy()
    pis = [polarity(u)]
    norms = [float(np.linalg.norm(u))]
    dt_out = final_operator_time / output_steps
    sub = max(1, int(math.ceil(dt_out * max(rate_inf, 1e-12) / max_dt_rate)))
    dt = dt_out / sub
    for _ in range(output_steps):
        for _ in range(sub):
            u = _rk4_step(J,u,dt)
            if not np.isfinite(u).all():
                raise FloatingPointError("non-finite RK4 state")
            nu = np.linalg.norm(u)
            if nu > 1e100:
                raise FloatingPointError("linear state overflow")
        pis.append(polarity(u))
        norms.append(float(np.linalg.norm(u)))
    pis = np.array(pis)
    late = pis[max(1, len(pis)//2):]
    return {
        "pi_initial": float(pis[0]),
        "pi_final": float(pis[-1]),
        "pi_mean_late": float(np.mean(late)),
        "pi_median_late": float(np.median(late)),
        "pi_peak_abs": float(np.max(np.abs(pis[1:]))),
        "state_norm_growth": float(norms[-1]/max(norms[0],1e-30)),
        "rk4_subcycles_per_output": int(sub),
    }


def candidate_metrics(curve: np.ndarray, cfg: dict) -> dict:
    require_native()
    core = float(cfg["core_fraction"])
    fd_eps = float(cfg.get("fd_eps_fraction", 2e-5))
    xi = tube_helicity_xi(curve, core, int(cfg.get("helicity_radial_nodes",3)), int(cfg.get("helicity_angles",8)))
    wr = float(writhe(curve, 1e-10))
    J, opmeta = build_operator(curve, core, fd_eps)
    eig = np.linalg.eigvals(J)
    spectral_scale = max(float(np.max(np.abs(eig))), 1e-15)
    spectral = {
        "max_real": float(np.max(eig.real)),
        "min_real": float(np.min(eig.real)),
        "spectral_radius": float(np.max(np.abs(eig))),
        "eigenvalues": [[float(z.real), float(z.imag)] for z in eig],
        "scale": spectral_scale
    }
    vals = []
    for center in cfg.get("excitation_centers", [0.25,0.75]):
        for mode in cfg.get("carrier_modes", [3]):
            u0 = initial_packet(len(curve), float(center), float(cfg.get("packet_width",0.08)), int(mode))
            dyn = evolve_packet(
                J,u0,float(cfg.get("final_operator_time",3.0)),int(cfg.get("output_steps",120)),
                float(cfg.get("max_dt_rate",0.08)),opmeta["normalized_inf_rate"]
            )
            dyn["center"] = float(center); dyn["mode"] = int(mode)
            vals.append(dyn)
    pi = np.array([v["pi_mean_late"] for v in vals],dtype=float)
    return {
        "xi_helicity_tube": float(xi),
        "writhe": wr,
        "transport_pi": float(np.mean(pi)),
        "transport_pi_std_over_excitations": float(np.std(pi)),
        "transport_pi_abs_mean": float(np.mean(np.abs(pi))),
        "operator": opmeta,
        "spectrum": spectral,
        "excitations": vals,
    }
