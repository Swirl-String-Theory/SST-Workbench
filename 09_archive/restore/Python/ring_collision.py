"""
Head-on vortex-ring collision in a rotating cylinder (superfluid-style filament model)
======================================================================================
Model: Schwarz-type vortex filament method.
 - Desingularized Biot-Savart (Rosenhead-Moore kernel, core radius a).
 - Ambient rotation Omega*z_hat imposed as a FIXED solid-body background flow
   u_bg = Omega x r  (equivalent to uniform ambient vorticity 2*Omega*z_hat).
 - Ad-hoc reconnections when filaments approach within d_rec with antiparallel tangents.
 - No walls (image vorticity neglected), no mutual friction (T = 0).

Geometry: cylinder R_cyl = 0.25 m, H = 1 m.
Two "vortex guns": bottom (0,0,0) fires a ring upward, top (0,0,1) fires one
downward. Same |Gamma|, opposite orientation -> exact head-on collision.

Diagnostics: relative vorticity support (= filaments; absolute adds 2*Omega*z),
writhe, linking number, filament helicity H_fil = Gamma^2 (Wr + 2 Lk),
mixed background helicity  H_mix = Gamma * 2*Omega * sum(A_z),
vertical impulse I_z ~ Gamma * sum(A_z)  (conservation check).
"""

import numpy as np
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
from matplotlib.animation import PillowWriter
import time, json, os

rng = np.random.default_rng(7)
EVENTS = []
SIM_T = [0.0]

# ----------------------------- parameters -----------------------------
Omega   = 1.0          # rad/s background rotation
R_cyl   = 0.25         # m
H_cyl   = 1.0          # m
Gamma   = 2.0e-3       # m^2/s  (both rings, same magnitude)
a_core  = 1.5e-3       # m core radius (RM regularization)
a2      = a_core**2
alpha_f = 0.0          # mutual friction (Schwarz, ~He-II at 1.6 K); damps Kelvin waves
R0      = 0.04         # m initial ring radius
z_bot, z_top = 0.06, 0.94
N0      = 96           # nodes per ring initially
m_pert, eps_pert = 3, 0.02   # azimuthal seed perturbation
eps_z   = 0.008              # axial contact-lobe seed (m lobes, antiphase)
dt      = 0.02         # s
T_end   = 60.0         # s
ds0     = 2*np.pi*R0/N0
ds_max, ds_min = 1.7*ds0, 0.45*ds0
d_rec   = 2.5*a_core
NODE_CAP  = 600
REC_EVERY = 5
DIAG_EVERY = 25        # 0.5 s
FRAME_EVERY = 20       # 0.4 s
OUT = "/home/claude/out"
os.makedirs(OUT, exist_ok=True)

# ----------------------------- initial loops --------------------------
def make_ring(zc, upward=True, phase=0.0, zsign=+1.0):
    th = np.linspace(0, 2*np.pi, N0, endpoint=False)
    if not upward:
        th = th[::-1]  # reversed traversal -> opposite circulation orientation
    r = R0*(1.0 + eps_pert*np.cos(m_pert*th + phase))
    z = zc + zsign*eps_z*np.cos(m_pert*th)   # antiphase -> m contact lobes
    return np.column_stack([r*np.cos(th), r*np.sin(th), z])

loops  = [make_ring(z_bot, True, 0.0, +1.0), make_ring(z_top, False, 0.0, -1.0)]
colors = [np.array([0.90, 0.30, 0.05]), np.array([0.05, 0.35, 0.90])]  # oranje / blauw
ages   = [99, 99]              # outer steps since creation (reconnection cooldown)
COOLDOWN = 3

# ----------------------------- kinematics ------------------------------
def tangents(P):
    T = np.roll(P, -1, axis=0) - np.roll(P, 1, axis=0)
    return T/np.linalg.norm(T, axis=1)[:, None]

def segments(loops):
    mids, dls = [], []
    for P in loops:
        Q = np.roll(P, -1, axis=0)
        mids.append(0.5*(P+Q)); dls.append(Q-P)
    return np.vstack(mids), np.vstack(dls)

def wall_image(mids, dls):
    """Local plane-mirror image across the cylinder wall r = R_cyl.
    x_img = x + 2*(R_cyl - r)*r_hat ; dl_img = dl - 2*(dl . r_hat)*r_hat.
    Enforces u_r ~ 0 at the wall (exact for a plane, approximate for the
    cylinder: curvature neglected)."""
    r = np.sqrt(mids[:, 0]**2 + mids[:, 1]**2)
    r = np.maximum(r, 1e-9)
    rhat = np.zeros_like(mids)
    rhat[:, 0] = mids[:, 0]/r
    rhat[:, 1] = mids[:, 1]/r
    mids_i = mids + 2*(R_cyl - r)[:, None]*rhat
    dls_i = dls - 2*np.einsum('ij,ij->i', dls, rhat)[:, None]*rhat
    return mids_i, dls_i

def velocity(X, loops, chunk=250):
    mids, dls = segments(loops)
    mi, di = wall_image(mids, dls)
    mids = np.vstack([mids, mi]); dls = np.vstack([dls, di])
    U = np.empty_like(X)
    pref = Gamma/(4*np.pi)
    for s in range(0, len(X), chunk):
        x = X[s:s+chunk]
        r = x[:, None, :] - mids[None, :, :]
        d2 = np.einsum('ijk,ijk->ij', r, r) + a2
        cr = np.cross(np.broadcast_to(dls, r.shape), r)
        U[s:s+chunk] = pref*np.einsum('ijk,ij->ik', cr, d2**-1.5)
    # mutual friction (normal fluid co-rotates => u_n - u_s = -u_ind):
    # u_L = u_ind + alpha_f * (s_hat x (-u_ind)) = u_ind - alpha_f * (s_hat x u_ind)
    if alpha_f > 0:
        tans = np.vstack([tangents(P) for P in loops])
        U -= alpha_f*np.cross(tans, U)
    # background solid-body rotation
    U[:, 0] += -Omega*X[:, 1]
    U[:, 1] +=  Omega*X[:, 0]
    return U

def flat(loops):
    return np.vstack(loops), np.cumsum([len(P) for P in loops])

def unflat(X, cuts):
    out, s = [], 0
    for c in cuts:
        out.append(X[s:c]); s = c
    return out

def step(loops, h):
    X, cuts = flat(loops)
    k1 = velocity(X, loops)
    Xm = X + 0.5*h*k1
    lm = unflat(Xm, cuts)
    k2 = velocity(Xm, lm)
    return unflat(X + h*k2, cuts)

# ----------------------------- remeshing -------------------------------
def remesh_loop(P, dmin, dmax):
    n = len(P)
    Q = np.roll(P, -1, axis=0)
    L = np.linalg.norm(Q-P, axis=1)
    new = []
    i = 0
    while i < n:
        new.append(P[i])
        if L[i] > dmax:
            new.append(0.5*(P[i]+Q[i]))
            i += 1
        elif L[i] < dmin and n - (len(new)) > 5:
            i += 2  # drop next node (merge)
        else:
            i += 1
    return np.array(new)

def smooth(loops, lam=0.015):
    """Curvature-selective damping: kills grid-scale Kelvin waves (~(1-2*lam) per
    application at wavelength 2*ds), barely touches ring-scale motion.
    Physical reading: phonon emission at core scale."""
    out = []
    for P in loops:
        out.append(P + lam*(0.5*(np.roll(P, -1, 0) + np.roll(P, 1, 0)) - P))
    return out

def smooth(loops, lam=0.01):
    """Curvature-selective damping: kills grid-scale Kelvin waves,
    barely affects large rings (proxy for phonon emission at core scale)."""
    out = []
    for P in loops:
        out.append(P + lam*(0.5*(np.roll(P, -1, 0) + np.roll(P, 1, 0)) - P))
    return out

def smooth(loops, lam=0.02):
    """Curvature (Laplacian) smoothing: damps grid-scale Kelvin waves hard,
    large-scale rings only ~lam*ds^2/(2R) per application (model for phonon
    emission at the core scale). Both spurious discrete polarizations decay."""
    out = []
    for P in loops:
        out.append(P + lam*(0.5*(np.roll(P, -1, 0) + np.roll(P, 1, 0)) - P))
    return out

LAM_SMOOTH = 0.015
def smooth(loops, lam=LAM_SMOOTH):
    out = []
    for P in loops:
        out.append(P + lam*(0.5*(np.roll(P, -1, 0) + np.roll(P, 1, 0)) - P))
    return out

def remesh(loops, colors, ages):
    killed = 0.0
    for _ in range(4):
        total = sum(len(P) for P in loops)
        scale = max(1.0, total/NODE_CAP)     # coarsen globally if over cap
        lo, hi = ds_min*scale, ds_max*scale
        out_l, out_c, out_a = [], [], []
        for P, c, ag in zip(loops, colors, ages):
            P = remesh_loop(P, lo, hi)
            # clamp nodes inside the wall (crude model of wall-sliding)
            r = np.sqrt(P[:, 0]**2 + P[:, 1]**2)
            over = r > R_cyl - a_core
            if over.any():
                fac = (R_cyl - a_core)/r[over]
                P[over, 0] *= fac; P[over, 1] *= fac
            Q = np.roll(P, -1, axis=0)
            length = np.linalg.norm(Q-P, axis=1).sum()
            rmean = np.sqrt(P[:, 0]**2 + P[:, 1]**2).mean()
            wall_hug = rmean > R_cyl - 5*a_core and length < 0.3
            if len(P) < 6 or length < 12*a_core or wall_hug:
                killed += length          # annihilated (small loop or at wall)
                continue
            out_l.append(P); out_c.append(c); out_a.append(ag)
        loops, colors, ages = out_l, out_c, out_a
        if sum(len(P) for P in loops) <= 1.2*NODE_CAP:
            break
    if sum(len(P) for P in loops) > 1.5*NODE_CAP:   # hard decimation
        loops = [P[::2] if len(P) > 12 else P for P in loops]
    return loops, colors, ages, killed

# ----------------------------- reconnection ----------------------------
def try_reconnect(loops, colors, ages):
    if len(loops) == 0 or sum(len(P) for P in loops) < 12:
        return loops, colors, 0
    X, cuts = flat(loops)
    ids = np.concatenate([np.full(len(P), k) for k, P in enumerate(loops)])
    idx = np.concatenate([np.arange(len(P)) for P in loops])
    tree = cKDTree(X)
    pairs = tree.query_pairs(d_rec, output_type='ndarray')
    if len(pairs) == 0:
        return loops, colors, ages, 0
    tans = np.vstack([tangents(P) for P in loops])
    best, bestd = None, np.inf
    for p, q in pairs:
        lp, lq = ids[p], ids[q]
        if len(loops[lp]) < 40 or len(loops[lq]) < 40:
            continue   # kleine ringlets zijn stabiel (vliegen weg)
        if lp == lq:
            n = len(loops[lp]); di = abs(idx[p]-idx[q]); di = min(di, n-di)
            if di <= 5:
                continue
        if np.dot(tans[p], tans[q]) > -0.2:
            continue
        # Schwarz-criterium: reconnectie moet totale lengte verminderen
        A, B = loops[lp], loops[lq]
        ai, bj = idx[p], idx[q]
        a1 = A[(ai+1) % len(A)]; b1 = B[(bj+1) % len(B)]
        old_len = np.linalg.norm(A[ai]-a1) + np.linalg.norm(B[bj]-b1)
        new_len = np.linalg.norm(A[ai]-b1) + np.linalg.norm(B[bj]-a1)
        if new_len >= 0.95*old_len:
            continue
        d = np.linalg.norm(X[p]-X[q])
        if d < bestd:
            bestd, best = d, (p, q)
    if best is None:
        return loops, colors, ages, 0
    p, q = best
    lp, lq, i, j = ids[p], ids[q], idx[p], idx[q]
    new_loops = [P for k, P in enumerate(loops) if k not in (lp, lq)]
    new_cols  = [c for k, c in enumerate(colors) if k not in (lp, lq)]
    new_ages  = [a for k, a in enumerate(ages) if k not in (lp, lq)]
    if lp != lq:                                # merge two loops
        A, B = loops[lp], loops[lq]
        merged = np.vstack([A[:i+1], B[j+1:], B[:j+1], A[i+1:]])
        for _ in range(3):   # relax the reconnection kink
            merged = merged + 0.25*(0.5*(np.roll(merged, -1, 0)+np.roll(merged, 1, 0)) - merged)
        new_loops.append(merged)
        new_cols.append(0.5*(colors[lp]+colors[lq]))
        new_ages.append(0)
        EVENTS.append((SIM_T[0], "merge", len(A), len(B)))
    else:                                       # split one loop
        A = loops[lp]; i, j = sorted((i, j))
        L1, L2 = A[i+1:j+1], np.vstack([A[j+1:], A[:i+1]])
        base = colors[lp]
        EVENTS.append((SIM_T[0], "split", len(L1), len(L2)))
        for L in (L1, L2):
            if len(L) >= 3:
                for _ in range(3):
                    L = L + 0.25*(0.5*(np.roll(L, -1, 0)+np.roll(L, 1, 0)) - L)
                new_loops.append(L)
                jit = np.clip(base + rng.uniform(-0.18, 0.18, 3), 0.05, 0.95)
                new_cols.append(jit)
                new_ages.append(0)
    return new_loops, new_cols, new_ages, 1

# ----------------------------- diagnostics -----------------------------
def loop_props(P):
    Q = np.roll(P, -1, axis=0)
    L = np.linalg.norm(Q-P, axis=1).sum()
    Az = 0.5*np.sum(P[:, 0]*Q[:, 1] - Q[:, 0]*P[:, 1])
    zc = P[:, 2].mean()
    rc = np.sqrt(P[:, 0]**2 + P[:, 1]**2).mean()
    return L, Az, zc, rc

def gauss_double(mA, tA, mB, tB, same):
    r = mA[:, None, :] - mB[None, :, :]
    d2 = np.einsum('ijk,ijk->ij', r, r)
    if same:
        np.fill_diagonal(d2, np.inf)
    cr = np.cross(tA[:, None, :], tB[None, :, :])
    val = np.einsum('ijk,ijk->ij', cr, r)*d2**-1.5
    return val.sum()/(4*np.pi)

def writhe(P):
    Q = np.roll(P, -1, axis=0)
    return gauss_double(0.5*(P+Q), Q-P, 0.5*(P+Q), Q-P, True)

def linking(P, S):
    Q, T = np.roll(P, -1, 0), np.roll(S, -1, 0)
    return gauss_double(0.5*(P+Q), Q-P, 0.5*(S+T), T-S, False)

# ----------------------------- adaptive dt -----------------------------
def global_min_sep(loops):
    """Minimum separation between non-adjacent filament points
    (cross-loop and self, excluding <=3 along-loop neighbours)."""
    X, cuts = flat(loops)
    ids = np.concatenate([np.full(len(P), k) for k, P in enumerate(loops)])
    idx = np.concatenate([np.arange(len(P)) for P in loops])
    sizes = np.array([len(P) for P in loops])
    tree = cKDTree(X)
    k = min(7, len(X))
    dists, nn = tree.query(X, k=k)
    best = np.inf
    for c in range(1, k):
        j = nn[:, c]
        same = ids == ids[j]
        n = sizes[ids]
        di = np.abs(idx - idx[j]); di = np.minimum(di, n - di)
        ok = (~same) | (di > 3)
        if ok.any():
            best = min(best, dists[ok, c].min())
    return best

def stable_dt(dmin):
    d = max(dmin, a_core)
    return float(np.clip(0.25*2*np.pi*d*d/Gamma, 2e-3, dt))

# ----------------------------- main loop -------------------------------
nsteps = int(T_end/dt)
diag = dict(t=[], nloops=[], Ltot=[], Wr=[], Lk=[], Hfil=[], Hmix=[],
            Iz=[], mind=[], killed=[], zc=[], rc=[], nrec=[])
frames = []
killed_total, nrec_total = 0.0, 0
t0 = time.time()

t = 0.0
next_frame, next_diag, next_log = 0.0, 0.0, 0.0
FRAME_DT, DIAG_DT, LOG_DT = 0.4, 0.5, 5.0

while t <= T_end + 1e-9:
    if t >= next_frame - 1e-9:
        frames.append((t, [P.copy() for P in loops], [c.copy() for c in colors]))
        next_frame += FRAME_DT
    if t >= next_diag - 1e-9:
        props = [loop_props(P) for P in loops]
        Ltot = sum(p[0] for p in props)
        Az   = [p[1] for p in props]
        Wr   = sum(writhe(P) for P in loops)
        Lk   = 0.0
        for a in range(len(loops)):
            for b in range(a+1, len(loops)):
                Lk += linking(loops[a], loops[b])
        mind = np.inf
        if len(loops) > 1:
            trees = [cKDTree(P) for P in loops]
            for a in range(len(loops)):
                for b in range(a+1, len(loops)):
                    dd, _ = trees[b].query(loops[a], k=1)
                    mind = min(mind, dd.min())
        diag['t'].append(t); diag['nloops'].append(len(loops))
        diag['Ltot'].append(Ltot); diag['Wr'].append(Wr); diag['Lk'].append(Lk)
        diag['Hfil'].append(Gamma**2*(Wr + 2*Lk))
        diag['Hmix'].append(Gamma*2*Omega*sum(Az))
        diag['Iz'].append(Gamma*sum(Az))
        diag['mind'].append(mind if np.isfinite(mind) else np.nan)
        diag['killed'].append(killed_total); diag['nrec'].append(nrec_total)
        diag['zc'].append([p[2] for p in props]); diag['rc'].append([p[3] for p in props])
        next_diag += DIAG_DT
        if t >= next_log - 1e-9:
            print(f"t={t:6.2f}s loops={len(loops)} nodes={sum(len(P) for P in loops)} "
                  f"L={Ltot:.3f} m mind={mind if np.isfinite(mind) else -1:.4f} "
                  f"rec={nrec_total} wall={time.time()-t0:.0f}s", flush=True)
            next_log += LOG_DT
    if t >= T_end - 1e-9:
        break
    # --- adaptive substepping over one outer interval dt ---
    remaining = dt
    SIM_T[0] = t
    while remaining > 1e-12 and len(loops) > 0:
        dmin = global_min_sep(loops) if len(loops) > 0 else np.inf
        h = min(stable_dt(dmin), remaining)
        loops = step(loops, h)
        remaining -= h
        if dmin < 3*d_rec:                     # close approach: reconnect eagerly
            for _ in range(4):
                loops, colors, ages, did = try_reconnect(loops, colors, ages)
                nrec_total += did
                if not did:
                    break
            loops = smooth(loops, 0.008)
            loops, colors, ages, killed = remesh(loops, colors, ages)
            killed_total += killed
        if len(loops) == 0:
            break
    if len(loops) > 0 and int(round(t/dt)) % REC_EVERY == 0:
        for _ in range(6):
            loops, colors, ages, did = try_reconnect(loops, colors, ages)
            nrec_total += did
            if not did:
                break
    if len(loops) > 0:
        if int(round(t/dt)) % 5 == 0:
            loops = smooth(loops)
        loops, colors, ages, killed = remesh(loops, colors, ages)
        killed_total += killed
    ages = [a+1 for a in ages]
    t += dt
    if len(loops) == 0:
        print("All loops annihilated at t=%.2f" % t)
        break

print(f"done: {time.time()-t0:.0f} s wall, {nrec_total} reconnections")
np.save(os.path.join(OUT, "frames.npy"), np.array(len(frames)))
import pickle
with open(os.path.join(OUT, "data.pkl"), "wb") as f:
    pickle.dump(dict(diag=diag, frames=frames, events=EVENTS,
                     params=dict(Omega=Omega, Gamma=Gamma, a=a_core, R0=R0,
                                 dt=dt, d_rec=d_rec)), f)
