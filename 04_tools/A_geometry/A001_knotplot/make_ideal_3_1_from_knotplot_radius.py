#!/usr/bin/env python3
"""
make_ideal_3_1_from_knotplot_radius.py

Convert a KnotPlot relaxed xyz export for the trefoil into an Ideal.txt-style
AB/Fourier record with Id="3:1:1" using the common ropelength convention bridge:

    KnotPlot / radius-thickness convention:  tube radius tau = 1, L ~ 32.7457
    Gilbert Ideal.txt diameter convention:  tube diameter D = 1, L ~ 16.3729

If the KnotPlot curve has already been scaled so tau=1, the conversion to
Ideal.txt D=1 is simply a factor 1/2 coordinate scaling. This script therefore
DOES NOT estimate D from minimum point distance; it trusts the KnotPlot radius
normalization supplied by --kp-radius.

Usage:
    python make_ideal_3_1_from_knotplot_radius.py trefoil_safe_003.txt --out ideal_3_1_from_kp_radius.txt

Optional:
    --modes 64        Fourier modes to write
    --resample 4096   arclength samples used before fitting
    --kp-radius 1.0   KnotPlot tube radius unit; D_before = 2*kp_radius
"""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
import numpy as np

TARGET_ID = "3:1:1"
TARGET_CONWAY = "3"
TARGET_GILBERT_L = 16.372861


def split_floats(line: str):
    out = []
    for tok in re.split(r"[,;\s]+", line.strip()):
        if not tok:
            continue
        try:
            out.append(float(tok))
        except ValueError:
            pass
    return out


def read_xyz(path: Path) -> np.ndarray:
    pts = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("%"):
                continue
            vals = split_floats(s)
            if len(vals) >= 3:
                pts.append(vals[:3])
    if len(pts) < 4:
        raise ValueError(f"{path}: expected xyz point list, got {len(pts)} rows")
    pts = np.asarray(pts, dtype=float)
    if np.linalg.norm(pts[0] - pts[-1]) < 1e-12:
        pts = pts[:-1]
    return pts


def closed_length(pts: np.ndarray) -> float:
    return float(np.linalg.norm(np.roll(pts, -1, axis=0) - pts, axis=1).sum())


def edge_stats(pts: np.ndarray):
    e = np.linalg.norm(np.roll(pts, -1, axis=0) - pts, axis=1)
    return float(e.min()), float(e.max()), float(e.mean()), float(e.max() / e.min())


def resample_arclength(pts: np.ndarray, n: int) -> np.ndarray:
    seg = np.roll(pts, -1, axis=0) - pts
    sl = np.linalg.norm(seg, axis=1)
    if np.any(sl <= 0):
        keep = sl > 0
        pts = pts[keep]
        seg = np.roll(pts, -1, axis=0) - pts
        sl = np.linalg.norm(seg, axis=1)
    cum = np.concatenate([[0.0], np.cumsum(sl)])
    total = float(cum[-1])
    targets = np.linspace(0.0, total, n, endpoint=False)
    out = np.empty((n, 3), dtype=float)
    j = 0
    for i, s in enumerate(targets):
        while j + 1 < len(cum) and cum[j + 1] <= s:
            j += 1
        j = min(j, len(sl) - 1)
        u = 0.0 if sl[j] == 0 else (s - cum[j]) / sl[j]
        out[i] = (1-u)*pts[j] + u*pts[(j+1) % len(pts)]
    return out


def fit_fourier(samples: np.ndarray, modes: int):
    N = len(samples)
    modes = min(modes, max(1, N//2 - 1))
    t = 2*math.pi*np.arange(N)/N
    A = np.zeros((modes+1, 3), dtype=float)
    B = np.zeros((modes+1, 3), dtype=float)
    A[0] = 2*samples.mean(axis=0)
    for k in range(1, modes+1):
        c = np.cos(k*t)[:, None]
        s = np.sin(k*t)[:, None]
        A[k] = 2*np.mean(samples*c, axis=0)
        B[k] = 2*np.mean(samples*s, axis=0)
    return A, B


def eval_fourier(A, B, t, deriv=0):
    out = np.zeros((len(t), 3), dtype=float)
    if deriv == 0:
        out += A[0][None, :]/2
        for k in range(1, len(A)):
            out += A[k][None, :]*np.cos(k*t)[:, None] + B[k][None, :]*np.sin(k*t)[:, None]
    elif deriv == 1:
        for k in range(1, len(A)):
            out += -k*A[k][None, :]*np.sin(k*t)[:, None] + k*B[k][None, :]*np.cos(k*t)[:, None]
    else:
        raise ValueError("deriv must be 0 or 1")
    return out


def fourier_length(A, B, n=8192):
    t = np.linspace(0, 2*math.pi, n, endpoint=False)
    v = eval_fourier(A, B, t, deriv=1)
    return float(2*math.pi*np.mean(np.linalg.norm(v, axis=1)))


def phase_shift(A, B, phi):
    A2 = A.copy(); B2 = B.copy()
    for k in range(1, len(A)):
        c = math.cos(k*phi); s = math.sin(k*phi)
        Ak = A[k].copy(); Bk = B[k].copy()
        A2[k] = Ak*c + Bk*s
        B2[k] = -Ak*s + Bk*c
    return A2, B2


def rotate(A, B, R):
    return A @ R.T, B @ R.T


def standardize(A, B):
    # Approximate Gilbert orientation: center at origin, first harmonic aligned.
    A = A.copy(); B = B.copy()
    A[0] = 0; B[0] = 0
    if len(A) < 2:
        return A, B
    a2 = float(np.dot(A[1], A[1])); b2 = float(np.dot(B[1], B[1])); ab = float(np.dot(A[1], B[1]))
    phi = 0.5*math.atan2(-2*ab, b2-a2)
    A, B = phase_shift(A, B, phi)
    e1 = A[1].copy(); n1 = np.linalg.norm(e1)
    if n1 < 1e-14:
        return A, B
    e1 /= n1
    e2 = B[1] - np.dot(B[1], e1)*e1
    n2 = np.linalg.norm(e2)
    if n2 < 1e-14:
        tmp = np.array([1.0, 0, 0])
        if abs(np.dot(tmp, e1)) > 0.9:
            tmp = np.array([0, 1.0, 0])
        e2 = tmp - np.dot(tmp, e1)*e1
        n2 = np.linalg.norm(e2)
    e2 /= n2
    e3 = np.cross(e1, e2); e3 /= np.linalg.norm(e3)
    R = np.vstack([e1, e2, e3])
    A, B = rotate(A, B, R)
    if A[1,0] < 0:
        A[:,0] *= -1; B[:,0] *= -1
    if B[1,1] < 0:
        A[:,1] *= -1; B[:,1] *= -1
    A[np.abs(A) < 5e-13] = 0
    B[np.abs(B) < 5e-13] = 0
    return A, B


def fmt(v):
    return ",".join(f"{float(x): .9f}" for x in v)


def write_ab(path: Path, A, B, L, source: str, comment: str):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write('<DATA Title="KnotPlot radius-normalized trefoil to Ideal.txt AB" Author="make_ideal_3_1_from_knotplot_radius.py">\n')
        f.write(f'<!-- Source: {source} -->\n')
        f.write(f'<!-- {comment} -->\n')
        f.write(f'<AB Id="{TARGET_ID}" Conway="{TARGET_CONWAY}" L="{L:.6f}" D=" 1.000000">\n')
        for k in range(1, len(A)):
            if np.max(np.abs(A[k])) < 5e-12 and np.max(np.abs(B[k])) < 5e-12:
                continue
            f.write(f'  <Coeff I="{k:2d}" A="{fmt(A[k])}" B="{fmt(B[k])}" />\n')
        f.write('</AB>\n</DATA>\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("knotplot_txt", type=Path)
    ap.add_argument("--out", type=Path, default=Path("ideal_3_1_from_kp_radius.txt"))
    ap.add_argument("--modes", type=int, default=64)
    ap.add_argument("--resample", type=int, default=4096)
    ap.add_argument("--eval", type=int, default=8192)
    ap.add_argument("--kp-radius", type=float, default=1.0, help="KnotPlot thickness radius unit before conversion")
    ap.add_argument("--no-standardize", action="store_true")
    args = ap.parse_args()

    pts = read_xyz(args.knotplot_txt)
    L_raw = closed_length(pts)
    emin, emax, eavg, easpect = edge_stats(pts)
    D_before = 2.0 * args.kp_radius
    scale = 1.0 / D_before

    samples = resample_arclength(pts, args.resample) * scale
    A, B = fit_fourier(samples, args.modes)
    if not args.no_standardize:
        A, B = standardize(A, B)
    L_fit = fourier_length(A, B, args.eval)
    rel = (L_fit - TARGET_GILBERT_L)/TARGET_GILBERT_L

    comment = (f"KnotPlot tau={args.kp_radius:g} radius convention assumed; "
               f"coordinates scaled by {scale:.9g}; raw L={L_raw:.9f}; raw L/2tau={L_raw/D_before:.9f}; "
               f"Fourier L={L_fit:.9f}; rel.err vs Gilbert={rel:+.6%}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_ab(args.out, A, B, L_fit, str(args.knotplot_txt), comment)

    print(f"points                 : {len(pts)}")
    print(f"raw KnotPlot length    : {L_raw:.9f}")
    print(f"edge min/max/avg/aspect: {emin:.9f} / {emax:.9f} / {eavg:.9f} / {easpect:.6f}")
    print(f"assumed D before scale : {D_before:.9f}")
    print(f"diameter-conv L=L/D    : {L_raw/D_before:.9f}")
    print(f"Fourier AB L after fit : {L_fit:.9f}")
    print(f"Gilbert target L       : {TARGET_GILBERT_L:.9f}")
    print(f"relative error         : {rel:+.6%}")
    print(f"wrote                  : {args.out}")

if __name__ == "__main__":
    main()
