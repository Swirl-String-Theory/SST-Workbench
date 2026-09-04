from __future__ import annotations
import numpy as np
import pandas as pd


def _closed_arclength(x):
    d = np.roll(x, -1, axis=0) - x
    seg = np.linalg.norm(d, axis=1)
    L = float(seg.sum())
    s = np.r_[0.0, np.cumsum(seg[:-1])]
    return s, L


def resample_closed_curve(x, n):
    x = np.asarray(x, float)
    s, L = _closed_arclength(x)
    s_ext = np.r_[s, L]
    x_ext = np.vstack([x, x[0]])
    st = np.linspace(0.0, L, n, endpoint=False)
    out = np.column_stack([np.interp(st, s_ext, x_ext[:,j]) for j in range(3)])
    return out, L


def kabsch_align(moving, reference):
    a = moving - moving.mean(axis=0)
    b = reference - reference.mean(axis=0)
    H = a.T @ b
    U, _, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = Vt.T @ U.T
    return a @ R + reference.mean(axis=0)


def reference_frame(curve):
    t = np.roll(curve, -1, axis=0) - np.roll(curve, 1, axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-30)
    dt = np.roll(t, -1, axis=0) - np.roll(t, 1, axis=0)
    n = dt - (dt*t).sum(axis=1, keepdims=True)*t
    nn = np.linalg.norm(n, axis=1, keepdims=True)
    bad = nn[:,0] < 1e-12
    if np.any(bad):
        # deterministic fallback normal
        axis = np.zeros_like(t); axis[:,2] = 1.0
        alt = np.cross(t, axis)
        alt2 = np.cross(t, np.column_stack([np.ones(len(t)), np.zeros((len(t),2))]))
        use = np.linalg.norm(alt, axis=1) < 1e-8
        alt[use] = alt2[use]
        n[bad] = alt[bad]
        nn = np.linalg.norm(n, axis=1, keepdims=True)
    n /= np.maximum(nn, 1e-30)
    b = np.cross(t, n)
    b /= np.maximum(np.linalg.norm(b, axis=1, keepdims=True), 1e-30)
    return t, n, b


def trajectory_to_spectrum(times, xyz, min_peak_snr=5.0, low_k_fraction=0.4, exclude_lowest_omega_bins=1):
    times = np.asarray(times, float)
    xyz = np.asarray(xyz, float)
    T, N0, _ = xyz.shape
    # resample all frames to common point count and align rigid motion
    ref, L = resample_closed_curve(xyz[0], N0)
    _, nvec, bvec = reference_frame(ref)
    fields = np.empty((T, N0), np.complex128)
    aligned_xyz = np.empty_like(xyz)
    for ti in range(T):
        cur, _ = resample_closed_curve(xyz[ti], N0)
        cur = kabsch_align(cur, ref)
        aligned_xyz[ti] = cur
        d = cur - ref
        fields[ti] = (d*nvec).sum(axis=1) + 1j*(d*bvec).sum(axis=1)
    # uniform time interpolation if needed
    tu = np.linspace(times[0], times[-1], T)
    if np.max(np.abs(times-tu)) > 1e-6 * max(times[-1]-times[0], 1e-30):
        f2 = np.empty_like(fields)
        for j in range(N0):
            f2[:,j] = np.interp(tu, times, fields[:,j].real) + 1j*np.interp(tu, times, fields[:,j].imag)
        fields = f2
    dt = float(np.median(np.diff(tu)))
    ds = L / N0
    fields -= fields.mean(axis=0, keepdims=True)
    wt = np.hanning(T)[:,None]
    ws = np.hanning(N0)[None,:]
    F = np.fft.fft2(fields * wt * ws)
    power = np.abs(F)**2
    omega = 2*np.pi*np.fft.fftfreq(T, d=dt)
    k = 2*np.pi*np.fft.fftfreq(N0, d=ds)
    posw = np.where(omega > 0)[0]
    nonzero_k = np.where(k != 0)[0]
    k_abs = np.abs(k[nonzero_k])
    k_cut = np.quantile(k_abs, low_k_fraction)
    rows = []
    for ji in nonzero_k:
        if abs(k[ji]) > k_cut:
            continue
        col = power[posw, ji]
        if len(col) <= exclude_lowest_omega_bins:
            continue
        col2 = col.copy()
        col2[:exclude_lowest_omega_bins] = 0
        ii = int(np.argmax(col2))
        peak = float(col2[ii])
        med = float(np.median(col2[col2>0])) if np.any(col2>0) else 0.0
        snr = peak / max(med, 1e-300)
        if snr < min_peak_snr:
            continue
        wi = posw[ii]
        rows.append({"k_rad_m": float(k[ji]), "abs_k_rad_m": float(abs(k[ji])),
                     "omega_rad_s": float(omega[wi]), "power": peak, "snr": snr})
    if not rows:
        raise ValueError("No spectral ridge peaks survived SNR/low-k selection.")
    return pd.DataFrame(rows), {"length_m": L, "dt_s": dt, "frames": T, "points": N0}
