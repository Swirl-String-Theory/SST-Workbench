import math
import numpy as np


def _vdc(n, base):
    n = int(n)
    v = 0.0
    denom = 1.0
    while n:
        n, rem = divmod(n, int(base))
        denom *= base
        v += rem / denom
    return v


def quasi_uniform_rotations(count, offset=17):
    """Deterministic low-discrepancy SO(3) samples via a Halton/Shoemake map."""
    out = []
    for idx in range(int(offset), int(offset) + int(count)):
        u1, u2, u3 = _vdc(idx, 2), _vdc(idx, 3), _vdc(idx, 5)
        x = math.sqrt(1.0-u1) * math.sin(2.0*math.pi*u2)
        y = math.sqrt(1.0-u1) * math.cos(2.0*math.pi*u2)
        z = math.sqrt(u1) * math.sin(2.0*math.pi*u3)
        w = math.sqrt(u1) * math.cos(2.0*math.pi*u3)
        Q = np.array([
            [1-2*(y*y+z*z), 2*(x*y-z*w),   2*(x*z+y*w)],
            [2*(x*y+z*w),   1-2*(x*x+z*z), 2*(y*z-x*w)],
            [2*(x*z-y*w),   2*(y*z+x*w),   1-2*(x*x+y*y)],
        ], dtype=float)
        out.append(Q)
    return out


def hopf_cell(radius=1.0, points_per_loop=24, linked=True):
    """Two closed circular filaments. linked=True gives a Hopf link with |Lk|=1."""
    R = float(radius)
    n = int(points_per_loop)
    t = np.linspace(0.0, 2.0*math.pi, n, endpoint=False)
    a = np.column_stack((R*np.cos(t), R*np.sin(t), np.zeros_like(t)))
    if linked:
        b = np.column_stack((R + R*np.cos(t), np.zeros_like(t), R*np.sin(t)))
    else:
        # Geometrically matched but separated control: no linking.
        b = np.column_stack((3.5*R + R*np.cos(t), np.zeros_like(t), R*np.sin(t)))
    cell = np.stack((a, b), axis=0)
    return cell - np.mean(cell.reshape(-1, 3), axis=0)[None, None, :]


def rotate_cell(cell, Q):
    return np.asarray(cell, dtype=float) @ np.asarray(Q, dtype=float).T


def affine_cell(cell, F):
    x = np.asarray(cell, dtype=float)
    c = np.mean(x.reshape(-1, 3), axis=0)
    return (x-c) @ np.asarray(F, dtype=float).T + c


def _segments(cell, circulations):
    x = np.asarray(cell, dtype=float)
    g = np.asarray(circulations, dtype=float)
    if x.ndim != 3 or x.shape[-1] != 3:
        raise ValueError("cell must have shape (n_loops,n_points,3)")
    if len(g) != x.shape[0]:
        raise ValueError("circulations length must equal n_loops")
    mids, dls, gs = [], [], []
    for ell in range(x.shape[0]):
        p = x[ell]
        q = np.roll(p, -1, axis=0)
        mids.append(0.5*(p+q))
        dls.append(q-p)
        gs.append(np.full(len(p), g[ell], dtype=float))
    return np.vstack(mids), np.vstack(dls), np.concatenate(gs)


def filament_energy_python(cell, circulations=(1.0,1.0), core_radius=0.18):
    """Regularized filament Hamiltonian divided by fluid density.

    E/rho = (1/8pi) sum_ij Gamma_i Gamma_j dl_i.dl_j/sqrt(r_ij^2+a^2).
    Units are L^5/T^2 for dimensional input.
    """
    mids, dls, gs = _segments(cell, circulations)
    r = mids[:, None, :] - mids[None, :, :]
    den = np.sqrt(np.sum(r*r, axis=-1) + float(core_radius)**2)
    dot = dls @ dls.T
    gg = gs[:, None] * gs[None, :]
    return float(np.sum(gg*dot/den)/(8.0*math.pi))


def filament_velocity(cell, circulations=(1.0,1.0), core_radius=0.18):
    """Regularized Biot-Savart velocity at Lagrangian filament nodes."""
    x = np.asarray(cell, dtype=float)
    mids, dls, gs = _segments(x, circulations)
    pts = x.reshape(-1, 3)
    r = pts[:, None, :] - mids[None, :, :]
    den = (np.sum(r*r, axis=-1) + float(core_radius)**2)**1.5
    v = np.sum(np.cross(dls[None, :, :], r) * (gs[None, :, None]/den[..., None]), axis=1)
    return (v/(4.0*math.pi)).reshape(x.shape)


def rk4_step(cell, dt, circulations=(1.0,1.0), core_radius=0.18):
    x = np.asarray(cell, dtype=float)
    h = float(dt)
    k1 = filament_velocity(x, circulations, core_radius)
    k2 = filament_velocity(x+0.5*h*k1, circulations, core_radius)
    k3 = filament_velocity(x+0.5*h*k2, circulations, core_radius)
    k4 = filament_velocity(x+h*k3, circulations, core_radius)
    return x + (h/6.0)*(k1+2.0*k2+2.0*k3+k4)


def gauss_linking_number(loop_a, loop_b):
    a = np.asarray(loop_a, dtype=float)
    b = np.asarray(loop_b, dtype=float)
    aq = np.roll(a, -1, axis=0); bq = np.roll(b, -1, axis=0)
    da = aq-a; db = bq-b
    ma = 0.5*(a+aq); mb = 0.5*(b+bq)
    r = ma[:, None, :] - mb[None, :, :]
    num = np.einsum("ijk,ijk->ij", np.cross(da[:, None, :], db[None, :, :]), r)
    den = (np.sum(r*r, axis=-1) + 1.0e-24)**1.5
    return float(np.sum(num/den)/(4.0*math.pi))


def loop_area_normal(loop):
    p = np.asarray(loop, dtype=float)
    q = np.roll(p, -1, axis=0)
    area = 0.5*np.sum(np.cross(p, q), axis=0)
    n = float(np.linalg.norm(area))
    return area/n if n > 0.0 else np.zeros(3)


def orientation_tensor(cells):
    normals = []
    for cell in cells:
        for loop in cell:
            normals.append(loop_area_normal(loop))
    normals = np.asarray(normals, dtype=float)
    M = np.einsum("ni,nj->ij", normals, normals)/len(normals)
    return M, float(np.linalg.norm(M-np.eye(3)/3.0))


def segment_length_cv(cell):
    vals = []
    for loop in np.asarray(cell):
        ds = np.linalg.norm(np.roll(loop, -1, axis=0)-loop, axis=1)
        vals.append(float(np.std(ds)/max(np.mean(ds), 1e-300)))
    return max(vals, default=0.0)


def shape_relative_rms(a, b):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    # Remove centroid translation; labels are Lagrangian so no cyclic rematching is used.
    ac = a-np.mean(a.reshape(-1,3),axis=0)[None,None,:]
    bc = b-np.mean(b.reshape(-1,3),axis=0)[None,None,:]
    return float(np.linalg.norm((ac-bc).ravel())/max(np.linalg.norm(bc.ravel()),1e-300))
