#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
coil_fourier_check.py

Spatial Fourier checker for 3-phase / multi-lane coil geometries.

What it computes
----------------
1) Driven wire spectrum:
      S_m^wire = |Σ_j I_j Δl_j exp(-i m θ_j)| / Σ_j |I_j Δl_j|

2) Biot-Savart field spectrum on a circular probe ring:
      S_m^B = |Σ_k B_component(φ_k) exp(-i m φ_k)| / Σ_k |B_component(φ_k)|

3) Optional SST-style mode-speed table:
      f_lock = |m| v_ref / (2π R_eff n)
   This is ONLY a conditional speed-scaling table, not evidence by itself.

Built-in geometries
-------------------
- sawshape : SawShape bowl, 3 phase, default S=40, steps +11/-9
- rodin    : Rodin torus-knot 6-lane, default P=5,Q=12, 3 phase + mirrored
- starship : Starship 6-phase/ABC+anti based on SawShape S=9, steps +4/+4
- all      : compare all built-ins

Custom CSV input
----------------
Use --custom-csv path.csv for arbitrary coils. Expected columns:
  lane,x,y,z
Optional columns:
  phase_rad OR phase_deg, current
Rows are ordered points per lane. Units can be mm or arbitrary; use --units-to-m.

Example custom CSV:
  lane,x,y,z,phase_deg,current
  A,10,0,0,0,1
  A,9.9,1,0,0,1
  B,-5,8.66,0,120,1

Dependencies
------------
  pip install numpy pandas matplotlib

Example runs
------------
  python coil_fourier_check.py --geometry all --out-dir coil_fourier_out
  python coil_fourier_check.py --geometry rodin --rodin-P 5 --rodin-Q 12 --out-dir rodin_out
  python coil_fourier_check.py --geometry sawshape --saw-S 40 --saw-fwd 11 --saw-bwd -9 --out-dir saw_out
  python coil_fourier_check.py --custom-csv mycoil.csv --out-dir custom_out --probe-r-mm 25 --probe-z-mm 20
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# Canon/reference speed used only for optional mode-frequency table.
V_REF_DEFAULT = 1.09384563e6  # m/s

PathTuple = Tuple[str, np.ndarray, complex]


# -----------------------------------------------------------------------------
# Basic helpers
# -----------------------------------------------------------------------------

def phase_values(phase_mode: str) -> Dict[str, float]:
    """Return A/B/C drive phases in radians for ABC, ACB, or scalar tests."""
    if phase_mode.lower() == "abc":
        return {"A": 0.0, "B": 2*np.pi/3, "C": 4*np.pi/3}
    if phase_mode.lower() == "acb":
        return {"A": 0.0, "B": 4*np.pi/3, "C": 2*np.pi/3}
    if phase_mode.lower() in ("zero", "all_zero", "all0"):
        return {"A": 0.0, "B": 0.0, "C": 0.0}
    raise ValueError(f"Unknown phase_mode={phase_mode!r}; choose abc, acb, all_zero")


def alternating_skip_indices(S: int, step_fwd: int, step_bwd: int, n_pairs: int, start: int = 1) -> np.ndarray:
    idx = int(start)
    seq = [idx]
    for k in range(2*int(n_pairs)):
        if k % 2 == 0:
            idx = (idx + step_fwd - 1) % S + 1
        else:
            idx = (idx + step_bwd - 1) % S + 1
        seq.append(idx)
    return np.asarray(seq, dtype=int)


def r_profile(s: np.ndarray, Rb: float, Rt: float, profile: str = "Exponential", power: float = 2.2) -> np.ndarray:
    profile_l = profile.lower()
    if profile_l.startswith("exp"):
        return Rb + (Rt - Rb) * (s**power)
    if profile_l.startswith("inv"):
        return Rt - (Rt - Rb) * (s**power)
    return Rb + (Rt - Rb) * s


def segmentize_paths(paths: Sequence[PathTuple], decimate: int = 1) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Convert lane point paths into segment midpoints, segment vectors, labels, complex currents."""
    mids: List[np.ndarray] = []
    dls: List[np.ndarray] = []
    labels: List[str] = []
    currents: List[complex] = []
    dec = max(1, int(decimate))
    for name, pts, I_complex in paths:
        pts = np.asarray(pts, dtype=float)[::dec]
        if len(pts) < 2:
            continue
        dl = pts[1:] - pts[:-1]
        mid = 0.5 * (pts[1:] + pts[:-1])
        mids.append(mid)
        dls.append(dl)
        labels.extend([name] * len(mid))
        currents.extend([complex(I_complex)] * len(mid))
    if not mids:
        return np.empty((0, 3)), np.empty((0, 3)), np.asarray([]), np.asarray([], dtype=complex)
    return np.vstack(mids), np.vstack(dls), np.asarray(labels), np.asarray(currents, dtype=complex)


def outer_radius(paths: Sequence[PathTuple]) -> float:
    max_r = 0.0
    for _, pts, _ in paths:
        pts = np.asarray(pts)
        r = np.sqrt(pts[:, 0]**2 + pts[:, 1]**2)
        max_r = max(max_r, float(np.max(r)))
    return max_r


def z_span(paths: Sequence[PathTuple]) -> Tuple[float, float]:
    zmin, zmax = np.inf, -np.inf
    for _, pts, _ in paths:
        pts = np.asarray(pts)
        zmin = min(zmin, float(np.min(pts[:, 2])))
        zmax = max(zmax, float(np.max(pts[:, 2])))
    return zmin, zmax


# -----------------------------------------------------------------------------
# Spectrum calculations
# -----------------------------------------------------------------------------

def wire_spectrum(paths: Sequence[PathTuple], m_max: int = 80, decimate: int = 1) -> pd.DataFrame:
    mids, dls, labels, currents = segmentize_paths(paths, decimate=decimate)
    if len(mids) == 0:
        return pd.DataFrame(columns=["m", "S_wire"])
    theta = np.arctan2(mids[:, 1], mids[:, 0])
    weights = currents * np.linalg.norm(dls, axis=1)
    norm = float(np.sum(np.abs(weights)))
    rows = []
    for m in range(int(m_max) + 1):
        amp = np.sum(weights * np.exp(-1j*m*theta))
        rows.append({"m": m, "S_wire": float(np.abs(amp)/norm) if norm > 0 else 0.0})
    return pd.DataFrame(rows)


def biot_savart_complex_field(
    paths: Sequence[PathTuple],
    phi_grid: np.ndarray,
    r_probe: float,
    z_probe: float,
    decimate: int = 8,
) -> np.ndarray:
    """Relative Biot-Savart field. Constants μ0/4π are omitted because spectra are normalized."""
    mids, dls, labels, currents = segmentize_paths(paths, decimate=decimate)
    if len(mids) == 0:
        return np.zeros((len(phi_grid), 3), dtype=complex)

    obs = np.column_stack([
        r_probe * np.cos(phi_grid),
        r_probe * np.sin(phi_grid),
        np.full_like(phi_grid, z_probe),
    ])

    B = np.zeros((len(obs), 3), dtype=complex)
    for k, p in enumerate(obs):
        R = p[None, :] - mids
        Rnorm = np.linalg.norm(R, axis=1)
        mask = Rnorm > 1e-12
        cross = np.cross(dls[mask], R[mask])
        coef = currents[mask] / (Rnorm[mask]**3)
        B[k] = np.sum(cross * coef[:, None], axis=0)
    return B


def select_component(B: np.ndarray, phi: np.ndarray, component: str) -> np.ndarray:
    comp = component.lower()
    if comp == "br":
        e_r = np.column_stack([np.cos(phi), np.sin(phi), np.zeros_like(phi)])
        return np.sum(B * e_r, axis=1)
    if comp == "bphi":
        e_phi = np.column_stack([-np.sin(phi), np.cos(phi), np.zeros_like(phi)])
        return np.sum(B * e_phi, axis=1)
    if comp == "bmag":
        return np.sqrt(np.sum(np.abs(B)**2, axis=1))
    # default Bz
    return B[:, 2]


def field_spectrum(
    paths: Sequence[PathTuple],
    component: str = "Bz",
    m_max: int = 80,
    n_phi: int = 360,
    probe_r: Optional[float] = None,
    probe_z: Optional[float] = None,
    decimate: int = 8,
    remove_dc: bool = True,
) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, float, float]:
    r_outer = outer_radius(paths)
    zmin, zmax = z_span(paths)
    if probe_r is None:
        probe_r = 0.60 * r_outer
    if probe_z is None:
        # A useful default: above midplane/top by a fraction of outer radius.
        probe_z = 0.5*(zmin + zmax) + 0.60*r_outer

    phi = np.linspace(0.0, 2*np.pi, int(n_phi), endpoint=False)
    B = biot_savart_complex_field(paths, phi, probe_r, probe_z, decimate=decimate)
    signal = select_component(B, phi, component)
    if remove_dc:
        signal = signal - np.mean(signal)
    norm = np.sum(np.abs(signal))

    rows = []
    for m in range(int(m_max) + 1):
        amp = np.sum(signal * np.exp(-1j*m*phi))
        rows.append({"m": m, f"S_field_{component}": float(np.abs(amp)/norm) if norm > 0 else 0.0})
    return pd.DataFrame(rows), phi, signal, float(probe_r), float(probe_z)


def top_modes(df: pd.DataFrame, col: str, top_n: int = 10, exclude_dc: bool = True) -> pd.DataFrame:
    d = df.copy()
    if exclude_dc and "m" in d.columns:
        d = d[d["m"] > 0]
    return d.sort_values(col, ascending=False).head(int(top_n))


def mode_lock_table(geometry: str, top_field: pd.DataFrame, R_eff_m: float, v_ref: float, n_max: int = 16) -> pd.DataFrame:
    rows = []
    for m in top_field["m"].astype(int).tolist():
        for n in range(1, int(n_max) + 1):
            f = abs(m) * float(v_ref) / (n * 2*np.pi*R_eff_m) if R_eff_m > 0 else np.nan
            rows.append({
                "geometry": geometry,
                "m": m,
                "n": n,
                "R_eff_m": R_eff_m,
                "v_ref_m_s": v_ref,
                "f_lock_Hz": f,
                "f_lock_MHz": f/1e6,
                "note": "conditional speed-scaling table only; check LC/RF resonances independently",
            })
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Built-in geometry constructors
# -----------------------------------------------------------------------------

def build_curved_phase(
    seq: np.ndarray,
    S: int,
    Rb: float,
    Rt: float,
    Hc: float,
    samples_per_seg: int = 24,
    angle_offset: float = 0.0,
    profile: str = "Exponential",
    power: float = 2.2,
) -> np.ndarray:
    slot_angles_base = np.linspace(0, 2*np.pi, int(S), endpoint=False) - np.pi/2.0
    N = len(seq) - 1
    s_nodes = np.linspace(0, 1, N+1)
    r_nodes = r_profile(s_nodes, Rb, Rt, profile, power)
    z_nodes = s_nodes * Hc
    xs, ys, zs = [], [], []
    for k in range(N):
        i0, i1 = seq[k]-1, seq[k+1]-1
        a0 = slot_angles_base[i0] + angle_offset
        a1 = slot_angles_base[i1] + angle_offset
        da = (a1 - a0 + np.pi) % (2*np.pi) - np.pi
        a_line = a0 + np.linspace(0, 1, int(samples_per_seg), endpoint=False) * da
        r_line = np.linspace(r_nodes[k], r_nodes[k+1], int(samples_per_seg), endpoint=False)
        z_line = np.linspace(z_nodes[k], z_nodes[k+1], int(samples_per_seg), endpoint=False)
        xs.append(r_line*np.cos(a_line))
        ys.append(r_line*np.sin(a_line))
        zs.append(z_line)
    return np.column_stack([np.concatenate(xs), np.concatenate(ys), np.concatenate(zs)])


def make_sawshape_paths(args: argparse.Namespace, phase_map: Dict[str, float]) -> List[PathTuple]:
    seq = alternating_skip_indices(args.saw_S, args.saw_fwd, args.saw_bwd, args.saw_pairs, start=args.saw_start)
    scale = float(args.saw_scale_mm)
    paths: List[PathTuple] = []
    for label, offset in zip(["A", "B", "C"], [0.0, 2*np.pi/3, 4*np.pi/3]):
        pts = build_curved_phase(
            seq, args.saw_S, args.saw_Rb, args.saw_Rt, args.saw_Hc,
            samples_per_seg=args.samples_per_seg,
            angle_offset=offset,
            profile=args.profile,
            power=args.profile_power,
        )
        pts *= scale
        I = np.exp(1j*phase_map[label])
        paths.append((f"SawShape phase {label}", pts, I))
    return paths


def torus_lane(R_major: float, r_surface: float, p: int, q: int, t: np.ndarray, phase_angle: float = 0.0, mirror: bool = False) -> np.ndarray:
    theta = p*t + phase_angle
    phi = q*t
    x = (R_major + r_surface*np.cos(phi))*np.cos(theta)
    y = (R_major + r_surface*np.cos(phi))*np.sin(theta)
    z = r_surface*np.sin(phi)
    if mirror:
        z = -z
    return np.column_stack([x, y, z])


def make_rodin_paths(args: argparse.Namespace, phase_map: Dict[str, float]) -> List[PathTuple]:
    t = np.linspace(0.0, 2*np.pi, int(args.rodin_N), endpoint=True)
    paths: List[PathTuple] = []
    for label, offset in zip(["A", "B", "C"], [0.0, 2*np.pi/3, 4*np.pi/3]):
        I = np.exp(1j*phase_map[label])
        pts_top = torus_lane(args.rodin_R_major_mm, args.rodin_R_tube_mm, args.rodin_P, args.rodin_Q, t, phase_angle=offset, mirror=False)
        paths.append((f"Rodin phase {label} top", pts_top, I))
        if args.rodin_mirror:
            pts_bot = torus_lane(args.rodin_R_major_mm, args.rodin_R_tube_mm, args.rodin_P, args.rodin_Q, t, phase_angle=offset, mirror=True)
            # Same current phase by default; reverse sign with --rodin-mirror-opposed if desired.
            I_bot = -I if args.rodin_mirror_opposed else I
            paths.append((f"Rodin phase {label} bottom", pts_bot, I_bot))
    return paths


def make_starship_paths(args: argparse.Namespace, phase_map: Dict[str, float]) -> List[PathTuple]:
    STARSHIP_S = int(args.starship_S)
    seq = alternating_skip_indices(STARSHIP_S, args.starship_fwd, args.starship_bwd, args.starship_pairs, start=1)
    rot_angle = (2*np.pi/27)/3
    coil_angles = (np.linspace(0, 2*np.pi, 28)[:-1] - np.pi*1.5 + (2*np.pi/27))[::-1] + rot_angle
    segment_shift = (2*np.pi/27)/3
    specs = [
        (0,  0.0,   False, (1, 2, 3), "A"),
        (9,  0.0,   False, (1, 2, 3), "B"),
        (18, 0.0,   False, (1, 2, 3), "C"),
        (0,  np.pi, True,  (1, 2, 3), "a"),
        (9,  np.pi, True,  (1, 2, 3), "b"),
        (18, np.pi, True,  (1, 2, 3), "c"),
    ]
    tag_to_phase = {"A": "A", "B": "B", "C": "C", "a": "A", "b": "B", "c": "C"}

    def saw_to_27(saw_seq: np.ndarray, phase_offset_27: int) -> np.ndarray:
        return np.asarray([((int(s)*3 - phase_offset_27 - 1) % 27) + 1 for s in saw_seq], dtype=int)

    def build_starship_curved(seq_27: np.ndarray, phase_angle: float, segment: int) -> np.ndarray:
        N = len(seq_27) - 1
        s_nodes = np.linspace(0, 1, N+1)
        r_nodes = r_profile(s_nodes, args.saw_Rb, args.saw_Rt, args.profile, args.profile_power)
        z_nodes = s_nodes * args.saw_Hc
        seg = segment_shift*(segment - 1)
        xs, ys, zs = [], [], []
        for k in range(N):
            i0, i1 = int(seq_27[k])-1, int(seq_27[k+1])-1
            a0 = coil_angles[i0] + seg + phase_angle
            a1 = coil_angles[i1] + seg + phase_angle
            da = (a1 - a0 + np.pi) % (2*np.pi) - np.pi
            a_line = a0 + np.linspace(0, 1, int(args.samples_per_seg), endpoint=False) * da
            r_line = np.linspace(r_nodes[k], r_nodes[k+1], int(args.samples_per_seg), endpoint=False)
            z_line = np.linspace(z_nodes[k], z_nodes[k+1], int(args.samples_per_seg), endpoint=False)
            xs.append(r_line*np.cos(a_line))
            ys.append(r_line*np.sin(a_line))
            zs.append(z_line)
        pts = np.column_stack([np.concatenate(xs), np.concatenate(ys), np.concatenate(zs)])
        return pts * float(args.saw_scale_mm)

    paths: List[PathTuple] = []
    for off27, phase_angle, reverse, segs, tag in specs:
        path = seq[::-1] if reverse else seq
        seq_27 = saw_to_27(path, off27)
        base_phase = tag_to_phase[tag]
        I = np.exp(1j*phase_map[base_phase])
        if tag.islower() and args.starship_anti_opposed:
            I = -I
        for segment, strand in zip(segs, ["fwd", "neu", "bwd"]):
            pts = build_starship_curved(seq_27, phase_angle, segment)
            paths.append((f"Starship {tag} {strand}", pts, I))
    return paths


def load_custom_csv(path: Path, units_to_m: float, phase_mode: str) -> List[PathTuple]:
    """Load custom paths. Internally convert to mm for consistency with built-ins if units_to_m given."""
    df = pd.read_csv(path)
    required = {"lane", "x", "y", "z"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Custom CSV missing required columns: {sorted(missing)}")

    # Convert source units to mm because built-ins are mm. units_to_m means x*units_to_m = meters.
    scale_to_mm = float(units_to_m) * 1000.0
    paths: List[PathTuple] = []

    default_phase = phase_values(phase_mode)
    for lane, g in df.groupby("lane", sort=False):
        pts = g[["x", "y", "z"]].to_numpy(dtype=float) * scale_to_mm
        current = float(g["current"].iloc[0]) if "current" in g.columns else 1.0
        if "phase_rad" in g.columns:
            phase = float(g["phase_rad"].iloc[0])
        elif "phase_deg" in g.columns:
            phase = np.deg2rad(float(g["phase_deg"].iloc[0]))
        else:
            # If lane begins with A/B/C, apply phase_mode; else zero.
            key = str(lane)[0].upper()
            phase = default_phase.get(key, 0.0)
        paths.append((str(lane), pts, current*np.exp(1j*phase)))
    return paths


def get_geometries(args: argparse.Namespace) -> Dict[str, List[PathTuple]]:
    ph = phase_values(args.phase_mode)
    geoms: Dict[str, List[PathTuple]] = {}
    if args.custom_csv:
        name = Path(args.custom_csv).stem
        geoms[f"custom_{name}"] = load_custom_csv(Path(args.custom_csv), args.units_to_m, args.phase_mode)
        return geoms

    choices = ["sawshape", "rodin", "starship"] if args.geometry == "all" else [args.geometry]
    for geom in choices:
        if geom == "sawshape":
            geoms[f"SawShape_S{args.saw_S}_{args.saw_fwd}_{args.saw_bwd}"] = make_sawshape_paths(args, ph)
        elif geom == "rodin":
            geoms[f"Rodin_P{args.rodin_P}_Q{args.rodin_Q}"] = make_rodin_paths(args, ph)
        elif geom == "starship":
            geoms[f"Starship_S{args.starship_S}_{args.starship_fwd}_{args.starship_bwd}"] = make_starship_paths(args, ph)
        else:
            raise ValueError(f"Unknown geometry={geom}")
    return geoms


# -----------------------------------------------------------------------------
# Output/plotting
# -----------------------------------------------------------------------------

def save_lane_preview(paths: Sequence[PathTuple], out_png: Path, title: str) -> None:
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")
    for name, pts, I in paths:
        ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], lw=1.1, alpha=0.8, label=name[:24])
    all_pts = np.vstack([pts for _, pts, _ in paths])
    mins = all_pts.min(axis=0)
    maxs = all_pts.max(axis=0)
    span = float(np.max(maxs - mins))
    mid = 0.5*(mins + maxs)
    ax.set_xlim(mid[0]-span/2, mid[0]+span/2)
    ax.set_ylim(mid[1]-span/2, mid[1]+span/2)
    ax.set_zlim(mid[2]-span/2, mid[2]+span/2)
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("y [mm]")
    ax.set_zlabel("z [mm]")
    ax.set_title(title)
    ax.legend(fontsize=6, loc="upper left")
    plt.tight_layout()
    plt.savefig(out_png, dpi=170)
    plt.close(fig)


def run_analysis(args: argparse.Namespace) -> None:
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    geoms = get_geometries(args)
    all_wire = []
    all_field = []
    all_modes = []
    summary_rows = []
    profiles: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}

    for geom_name, paths in geoms.items():
        # Probe in mm. If explicit arguments absent, field_spectrum chooses defaults from geometry.
        probe_r = args.probe_r_mm if args.probe_r_mm is not None else None
        probe_z = args.probe_z_mm if args.probe_z_mm is not None else None

        wire_df = wire_spectrum(paths, m_max=args.m_max, decimate=args.decimate_wire)
        wire_df.insert(0, "geometry", geom_name)
        all_wire.append(wire_df)

        field_df, phi, sig, used_r_mm, used_z_mm = field_spectrum(
            paths,
            component=args.component,
            m_max=args.m_max,
            n_phi=args.n_phi,
            probe_r=probe_r,
            probe_z=probe_z,
            decimate=args.decimate_field,
            remove_dc=not args.keep_dc,
        )
        field_df.insert(0, "geometry", geom_name)
        all_field.append(field_df)
        profiles[geom_name] = (phi, sig)

        col_field = f"S_field_{args.component}"
        wire_top = top_modes(wire_df, "S_wire", args.top_n)
        field_top = top_modes(field_df, col_field, args.top_n)

        # Mode table uses actual probe radius as R_eff.
        R_eff_m = used_r_mm * 1e-3
        all_modes.append(mode_lock_table(geom_name, field_top.head(args.mode_table_top), R_eff_m, args.v_ref, n_max=args.n_max))

        summary_rows.append({
            "geometry": geom_name,
            "phase_mode": args.phase_mode,
            "outer_radius_mm": outer_radius(paths),
            "probe_r_mm": used_r_mm,
            "probe_z_mm": used_z_mm,
            "component": args.component,
            "top_wire_modes": ", ".join(f"{int(r.m)}:{r.S_wire:.4f}" for r in wire_top.itertuples()),
            "top_field_modes": ", ".join(f"{int(getattr(r, 'm'))}:{getattr(r, col_field):.4f}" for r in field_top.itertuples()),
        })

        if args.preview:
            safe = geom_name.replace("/", "_").replace(" ", "_")
            save_lane_preview(paths, out / f"{safe}_lane_preview.png", geom_name)

    wire_all = pd.concat(all_wire, ignore_index=True)
    field_all = pd.concat(all_field, ignore_index=True)
    modes_all = pd.concat(all_modes, ignore_index=True) if all_modes else pd.DataFrame()
    summary_df = pd.DataFrame(summary_rows)

    wire_all.to_csv(out / "wire_spectrum.csv", index=False)
    field_all.to_csv(out / "field_spectrum.csv", index=False)
    modes_all.to_csv(out / "mode_lock_frequencies.csv", index=False)
    summary_df.to_csv(out / "summary.csv", index=False)

    # Combined spectrum plot
    col_field = f"S_field_{args.component}"
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)
    for geom_name in geoms:
        d = wire_all[wire_all["geometry"] == geom_name]
        axes[0].plot(d["m"], d["S_wire"], marker="o", ms=2, lw=1, label=geom_name)
        d2 = field_all[field_all["geometry"] == geom_name]
        axes[1].plot(d2["m"], d2[col_field], marker="o", ms=2, lw=1, label=geom_name)
    axes[0].set_ylabel("S_wire")
    axes[0].set_title("Driven wire spatial Fourier spectrum")
    axes[0].grid(True, alpha=0.3)
    axes[1].set_xlabel("azimuthal mode m")
    axes[1].set_ylabel(col_field)
    axes[1].set_title(f"Biot-Savart {args.component} spectrum on probe ring")
    axes[1].grid(True, alpha=0.3)
    axes[0].legend(fontsize=8)
    axes[1].legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(out / "spatial_fourier_spectrum.png", dpi=180)
    plt.close(fig)

    # Field profiles plot
    fig, axes = plt.subplots(len(geoms), 1, figsize=(13, max(3, 3*len(geoms))), sharex=True)
    if len(geoms) == 1:
        axes = [axes]
    for ax, geom_name in zip(axes, geoms):
        phi, sig = profiles[geom_name]
        if np.iscomplexobj(sig):
            ax.plot(phi, np.real(sig), lw=1, label="Re(signal)")
            ax.plot(phi, np.imag(sig), lw=1, ls="--", label="Im(signal)")
        else:
            ax.plot(phi, sig, lw=1, label="signal")
        ax.set_ylabel(geom_name[:22])
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    axes[-1].set_xlabel("probe angle φ [rad]")
    plt.tight_layout()
    plt.savefig(out / "field_profiles.png", dpi=180)
    plt.close(fig)

    metadata = vars(args).copy()
    metadata["outputs"] = [
        "wire_spectrum.csv",
        "field_spectrum.csv",
        "mode_lock_frequencies.csv",
        "summary.csv",
        "spatial_fourier_spectrum.png",
        "field_profiles.png",
    ]
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(summary_df.to_string(index=False))
    print(f"\nWrote outputs to: {out.resolve()}")


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    ap.add_argument("--geometry", choices=["all", "sawshape", "rodin", "starship"], default="all")
    ap.add_argument("--custom-csv", default=None, help="custom coil CSV with columns lane,x,y,z[,phase_rad|phase_deg,current]")
    ap.add_argument("--units-to-m", type=float, default=1e-3, help="custom CSV unit scale: x * units_to_m = meters; default mm")
    ap.add_argument("--out-dir", default="coil_fourier_out")

    ap.add_argument("--phase-mode", choices=["abc", "acb", "all_zero"], default="abc", help="drive phase order")
    ap.add_argument("--component", choices=["Bz", "Br", "Bphi", "Bmag"], default="Bz")
    ap.add_argument("--m-max", type=int, default=80)
    ap.add_argument("--n-phi", type=int, default=360)
    ap.add_argument("--decimate-wire", type=int, default=1)
    ap.add_argument("--decimate-field", type=int, default=10)
    ap.add_argument("--probe-r-mm", type=float, default=None, help="probe ring radius in mm; default 0.60*outer_radius")
    ap.add_argument("--probe-z-mm", type=float, default=None, help="probe ring z in mm; default mid_z+0.60*outer_radius")
    ap.add_argument("--keep-dc", action="store_true", help="do not subtract mean field before Fourier spectrum")
    ap.add_argument("--top-n", type=int, default=10)
    ap.add_argument("--mode-table-top", type=int, default=5)
    ap.add_argument("--n-max", type=int, default=16)
    ap.add_argument("--v-ref", type=float, default=V_REF_DEFAULT, help="reference speed for conditional mode table only")
    ap.add_argument("--preview", action="store_true", help="also save 3D lane preview PNG(s)")

    # Shared smooth path params for SawShape and Starship
    ap.add_argument("--samples-per-seg", type=int, default=24)
    ap.add_argument("--profile", choices=["Exponential", "Linear", "Inverse Exp"], default="Exponential")
    ap.add_argument("--profile-power", type=float, default=2.2)

    # SawShape params
    ap.add_argument("--saw-S", type=int, default=40)
    ap.add_argument("--saw-fwd", type=int, default=11)
    ap.add_argument("--saw-bwd", type=int, default=-9)
    ap.add_argument("--saw-pairs", type=int, default=20)
    ap.add_argument("--saw-start", type=int, default=1)
    ap.add_argument("--saw-Rb", type=float, default=0.5)
    ap.add_argument("--saw-Rt", type=float, default=1.5)
    ap.add_argument("--saw-Hc", type=float, default=0.1)
    ap.add_argument("--saw-scale-mm", type=float, default=34.0/1.5, help="scale normalized Saw/Starship coordinates to mm")

    # Rodin params
    ap.add_argument("--rodin-R-major-mm", type=float, default=34.0)
    ap.add_argument("--rodin-R-tube-mm", type=float, default=9.0)
    ap.add_argument("--rodin-P", type=int, default=5)
    ap.add_argument("--rodin-Q", type=int, default=12)
    ap.add_argument("--rodin-N", type=int, default=1800)
    ap.add_argument("--rodin-mirror", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--rodin-mirror-opposed", action="store_true", help="make mirrored Rodin lane current sign-opposed")

    # Starship params
    ap.add_argument("--starship-S", type=int, default=9)
    ap.add_argument("--starship-fwd", type=int, default=4)
    ap.add_argument("--starship-bwd", type=int, default=4)
    ap.add_argument("--starship-pairs", type=int, default=20)
    ap.add_argument("--starship-anti-opposed", action="store_true", help="make anti set current sign-opposed")

    return ap


def main() -> None:
    args = build_arg_parser().parse_args()
    run_analysis(args)


if __name__ == "__main__":
    main()
