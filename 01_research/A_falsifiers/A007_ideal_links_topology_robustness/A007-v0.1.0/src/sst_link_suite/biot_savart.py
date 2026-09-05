from __future__ import annotations
from itertools import product
import numpy as np

def sign_configurations(m: int) -> list[tuple[int, ...]]:
    return list(product((-1, 1), repeat=m))

def _segments(points: np.ndarray):
    nxt = np.roll(points, -1, axis=0)
    return 0.5*(points+nxt), nxt-points

def velocity_at_points(
    eval_points: np.ndarray,
    source_points: np.ndarray,
    gamma: float,
    epsilon: float,
    eval_indices: np.ndarray | None = None,
    local_skip: int = 3,
    chunk: int = 128,
) -> np.ndarray:
    mid, dl = _segments(source_points)
    out = np.zeros_like(eval_points)
    nsrc = len(mid)
    eps2 = epsilon*epsilon
    for i0 in range(0, len(eval_points), chunk):
        i1 = min(i0+chunk, len(eval_points))
        diff = eval_points[i0:i1, None, :] - mid[None, :, :]
        num = np.cross(dl[None, :, :], diff)
        den = (np.einsum("ijk,ijk->ij", diff, diff) + eps2)**1.5
        kernel = num / np.maximum(den[..., None], 1e-30)
        if eval_indices is not None and len(eval_points) == len(source_points):
            rows = eval_indices[i0:i1, None]
            cols = np.arange(nsrc)[None, :]
            cyc = np.minimum((rows-cols) % nsrc, (cols-rows) % nsrc)
            kernel[cyc <= local_skip] = 0.0
        out[i0:i1] = gamma/(4*np.pi) * np.sum(kernel, axis=1)
    return out

def link_velocity(samples, signs: tuple[int, ...], epsilon: float) -> list[np.ndarray]:
    velocities = []
    for i, s in enumerate(samples):
        u = np.zeros_like(s.r)
        for j, src in enumerate(samples):
            indices = np.arange(len(s.r)) if i == j and len(s.r) == len(src.r) else None
            u += velocity_at_points(s.r, src.r, signs[j], epsilon, indices)
        velocities.append(u)
    return velocities

def _cross_matrix_for_omega(q: np.ndarray) -> np.ndarray:
    x, y, z = q
    return np.array([[0, z, -y], [-z, 0, x], [y, -x, 0]], dtype=float)

def fit_normal_rigid_motion(samples, velocities) -> dict:
    all_r = np.concatenate([s.r for s in samples], axis=0)
    center = all_r.mean(axis=0)
    rows, rhs = [], []
    normal_u2 = total_u2 = tang_u2 = 0.0
    for s, u in zip(samples, velocities):
        tang = s.d1 / np.maximum(np.linalg.norm(s.d1, axis=1)[:, None], 1e-30)
        for r, t, v in zip(s.r, tang, u):
            P = np.eye(3) - np.outer(t, t)
            A = np.concatenate([np.eye(3), _cross_matrix_for_omega(r-center)], axis=1)
            rows.append(P @ A)
            rhs.append(P @ v)
            vn = P @ v
            normal_u2 += float(vn @ vn)
            total_u2 += float(v @ v)
            tang_u2 += float((v @ t)**2)
    A = np.concatenate(rows, axis=0)
    b = np.concatenate(rhs, axis=0)
    x, *_ = np.linalg.lstsq(A, b, rcond=None)
    residual = A @ x - b
    rms = float(np.sqrt(np.mean(residual**2)))
    normal_rms = float(np.sqrt(normal_u2 / max(len(all_r), 1)))
    return {
        "translation": x[:3],
        "omega": x[3:],
        "translation_norm": float(np.linalg.norm(x[:3])),
        "omega_norm": float(np.linalg.norm(x[3:])),
        "normal_rigid_residual_rms": rms,
        "normal_velocity_rms": normal_rms,
        "relative_equilibrium_score": float(rms / max(normal_rms, 1e-30)),
        "tangential_energy_fraction": float(tang_u2 / max(total_u2, 1e-30)),
    }

def geometric_impulse(samples, signs: tuple[int, ...]) -> np.ndarray:
    out = np.zeros(3)
    for s, sign in zip(samples, signs):
        nxt = np.roll(s.r, -1, axis=0)
        out += 0.5 * sign * np.sum(np.cross(s.r, nxt-s.r), axis=0)
    return out

def neumann_energy_proxy(samples, signs: tuple[int, ...], epsilon: float, chunk: int = 128) -> float:
    segs = [_segments(s.r) for s in samples]
    total = 0.0
    for i, (mi, di) in enumerate(segs):
        for j, (mj, dj) in enumerate(segs):
            factor = signs[i]*signs[j]
            for i0 in range(0, len(mi), chunk):
                i1 = min(i0+chunk, len(mi))
                diff = mi[i0:i1, None, :] - mj[None, :, :]
                den = np.sqrt(np.einsum("ijk,ijk->ij", diff, diff) + epsilon**2)
                dot = np.einsum("ik,jk->ij", di[i0:i1], dj)
                if i == j:
                    rows = np.arange(i0, i1)[:, None]
                    cols = np.arange(len(mj))[None, :]
                    cyc = np.minimum((rows-cols) % len(mj), (cols-rows) % len(mj))
                    dot = np.where(cyc <= 2, 0.0, dot)
                total += factor * float(np.sum(dot / np.maximum(den, 1e-30)))
    return total/(8*np.pi)

def analyze_sign_configurations(samples, epsilons: list[float]) -> list[dict]:
    out = []
    for signs in sign_configurations(len(samples)):
        for eps in epsilons:
            vel = link_velocity(samples, signs, eps)
            fit = fit_normal_rigid_motion(samples, vel)
            impulse = geometric_impulse(samples, signs)
            out.append({
                "signs": list(signs),
                "epsilon_D": eps,
                **fit,
                "impulse_D2": impulse,
                "impulse_norm_D2": float(np.linalg.norm(impulse)),
                "neumann_energy_proxy": neumann_energy_proxy(samples, signs, eps),
            })
    return out
