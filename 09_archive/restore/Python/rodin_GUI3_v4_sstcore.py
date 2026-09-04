#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rodin_GUI3.py

Merged coil GUI for Rodin / SawShape / Starship experiments.

Fuses the intent of:
- rodin_GUI.py   : 3-phase Rodin torus-knot CW/CCW families, p/q cells, gap, Biot-Savart grid.
- rodin_GUI2.py  : generic coil presets, cached Biot-Savart, heatmap/quiver style controls.
- GUI-SawBowl.py : Straight/Curved SawShape + Straight/Curved Starship with bowl profile sliders.

Presets included:
- Solenoide
- Toroid
- Enkele winding
- Helmholtz
- Rodin-knot
- Rodin 3-phase CW/CCW
- Straight SawShape
- Curved SawShape
- Straight Starship
- Curved Starship

Exports:
- Save PNG of current view
- Export coil centerlines to CSV for external Fourier checks

Dependencies:
    pip install numpy matplotlib

Units:
- Generic coils use meters.
- Rodin 3-phase controls expose major diameter in cm and minor radius/gap in mm/cm as labelled.
- SawShape/Starship shape sliders are in mm and internally converted to meters.
"""

from __future__ import annotations

import csv
import math
import os
import importlib
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

MU0_4PI = 1e-7  # mu0/(4*pi)

Coil = Tuple[np.ndarray, str, str, str, float]  # pts, color, linestyle, label, current multiplier


# =============================================================================
# GUI helpers
# =============================================================================
class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, width=460):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0, width=width)
        self.vscroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vscroll.set)
        self.inner = ttk.Frame(self.canvas)
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.vscroll.pack(side="right", fill="y")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.inner_id, width=e.width))
        self._bind_mousewheel(self.canvas)
        self._bind_mousewheel(self.inner)

    def _bind_mousewheel(self, widget):
        widget.bind("<Enter>", lambda e: self._activate_mousewheel())
        widget.bind("<Leave>", lambda e: self._deactivate_mousewheel())

    def _activate_mousewheel(self):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _deactivate_mousewheel(self):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def _on_mousewheel_linux(self, event):
        self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")


class CollapsibleSection(ttk.Frame):
    def __init__(self, parent, title, initially_open=True):
        super().__init__(parent)
        self._open = tk.BooleanVar(value=initially_open)
        header = ttk.Frame(self)
        header.pack(fill=tk.X)
        self.btn = ttk.Button(header, width=2, command=self.toggle)
        self.btn.pack(side=tk.LEFT)
        ttk.Label(header, text=title, font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=(6, 0))
        self.body = ttk.Frame(self)
        self.body.pack(fill=tk.X, pady=(4, 8))
        self._refresh()

    def toggle(self):
        self._open.set(not self._open.get())
        self._refresh()

    def _refresh(self):
        if self._open.get():
            self.btn.configure(text="▼")
            self.body.pack(fill=tk.X, pady=(4, 8))
        else:
            self.btn.configure(text="►")
            self.body.forget()


@dataclass
class Grid3D:
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    X: np.ndarray
    Y: np.ndarray
    Z: np.ndarray


def make_grid(bounds: float, res: int) -> Grid3D:
    x = np.linspace(-bounds, bounds, res)
    y = np.linspace(-bounds, bounds, res)
    z = np.linspace(-bounds, bounds, res)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    return Grid3D(x=x, y=y, z=z, X=X, Y=Y, Z=Z)


def finite_polyline(points: np.ndarray) -> np.ndarray:
    pts = np.asarray(points, dtype=float)
    pts = pts[np.all(np.isfinite(pts), axis=1)]
    if len(pts) < 2:
        return np.zeros((0, 3), dtype=float)
    return pts


def try_import_sstcore():
    """Return SSTcore/sstcore module if a compiled binding is importable.

    The GUI uses only the wire-grid field kernel when available:
    ``biot_savart_wire_grid(X,Y,Z,wire_points,current)``.
    That kernel is segment-based and does not auto-close the polyline, so it is
    the correct SSTcore backend for open or guided coil centerlines.
    """
    for name in ("SSTcore", "sstcore"):
        try:
            return importlib.import_module(name)
        except Exception:
            pass
    return None


def biot_savart_wire_grid_sstcore(module, grid: Grid3D, polyline: np.ndarray, current: float):
    """Fast C++ backend via SSTcore.field_kernels.

    Important unit convention: SSTcore's field kernel uses mu0=1 internally
    and applies current/(4*pi). To reproduce SI Tesla from our NumPy kernel
    mu0*I/(4*pi), we pass current_core = mu0 * I.

    The current SSTcore field kernel has only an epsilon singularity guard, not
    the configurable GUI softening radius. Use the NumPy backend when you need
    softened near-wire fields for very close probe grids.
    """
    pts = np.ascontiguousarray(finite_polyline(polyline), dtype=float)
    if pts.shape[0] < 2 or abs(current) < 1e-30:
        z = np.zeros_like(grid.X, dtype=np.float64)
        return z.copy(), z.copy(), z.copy()
    if module is None or not hasattr(module, "biot_savart_wire_grid"):
        raise AttributeError("SSTcore backend has no biot_savart_wire_grid")

    current_core = (4.0 * math.pi * MU0_4PI) * float(current)  # mu0 * I
    bx, by, bz = module.biot_savart_wire_grid(
        np.ascontiguousarray(grid.X, dtype=float),
        np.ascontiguousarray(grid.Y, dtype=float),
        np.ascontiguousarray(grid.Z, dtype=float),
        pts,
        current_core,
    )
    return np.asarray(bx, dtype=float).reshape(grid.X.shape), \
           np.asarray(by, dtype=float).reshape(grid.X.shape), \
           np.asarray(bz, dtype=float).reshape(grid.X.shape)


# =============================================================================
# Coil geometry: generic coils
# =============================================================================
def torus_knot_polyline(R_major: float, r_minor: float, p: int, q: int, turns: int, n_points: int,
                        mirror: bool = False, theta_offset: float = 0.0, z_offset: float = 0.0) -> np.ndarray:
    p = int(max(1, p))
    q = int(max(1, q))
    turns = int(max(1, turns))
    n_points = int(max(200, n_points))
    t = np.linspace(0.0, 2.0 * np.pi * turns, n_points, endpoint=True)
    theta = p * t + theta_offset
    phi = q * t
    if mirror:
        phi = -phi
    x = (R_major + r_minor * np.cos(phi)) * np.cos(theta)
    y = (R_major + r_minor * np.cos(phi)) * np.sin(theta)
    z = r_minor * np.sin(phi) + z_offset
    return np.column_stack([x, y, z])


def generic_wire_points(kind: str, N: int, R: float, L: float, pts: int, p_knot: int, q_knot: int, turns_knot: int) -> np.ndarray:
    k = kind.lower()
    pts = int(max(200, pts))
    N = int(max(1, N))

    if k == "enkele winding":
        t = np.linspace(0, 2*np.pi, pts, endpoint=True)
        return np.column_stack([R*np.cos(t), R*np.sin(t), 0*t])

    if k == "helmholtz":
        sep = np.clip(L/4.0, 0.2*R, 1.6*R)
        t = np.linspace(0, 2*np.pi, max(100, pts//2), endpoint=True)
        x = R*np.cos(t)
        y = R*np.sin(t)
        p1 = np.column_stack([x, y, np.full_like(t, -sep/2)])
        p2 = np.column_stack([x, y, np.full_like(t, +sep/2)])
        # NaN separator for export/plot safety is not used; separate coils are cleaner elsewhere.
        return np.vstack([p1, p2])

    if k == "toroid":
        r = max(1e-9, R)
        a = max(1.5*r, 0.6*L)
        u = np.linspace(0, 2*np.pi, pts, endpoint=True)
        v = N*u
        x = (a + r*np.cos(v)) * np.cos(u)
        y = (a + r*np.cos(v)) * np.sin(u)
        z = r*np.sin(v)
        return np.column_stack([x, y, z])

    if k == "rodin-knot":
        r_minor = max(1e-9, R)
        R_major = max(1.5*r_minor, 0.6*L)
        return torus_knot_polyline(R_major, r_minor, p_knot, q_knot, turns_knot, pts)

    # Solenoide default
    pts_per_turn = max(60, pts // max(1, N))
    n_total = N * pts_per_turn
    t = np.linspace(0, 2*np.pi*N, n_total, endpoint=True)
    z = np.linspace(-L/2, L/2, n_total, endpoint=True)
    x = R*np.cos(t)
    y = R*np.sin(t)
    return np.column_stack([x, y, z])


# =============================================================================
# Coil geometry: Rodin 3-phase CW/CCW from rodin_GUI.py
# =============================================================================
def torus_knot_cellphase_polyline(
    R_major: float,
    r_minor: float,
    p: int,
    q: int,
    n_points: int = 1200,
    turns: int = 1,
    cell_phase_frac: float = 0.0,
    mirror: bool = False,
    z_offset: float = 0.0,
    theta_offset: float = 0.0,
) -> np.ndarray:
    p = int(max(1, p))
    q = int(max(1, q))
    turns = int(max(1, turns))
    n_points = int(max(200, n_points))
    t = np.linspace(0.0, 2.0*np.pi*turns, n_points, endpoint=True)
    dt_cell = float(cell_phase_frac) * (2.0*np.pi / q)
    tp = t + dt_cell
    theta = p*tp + float(theta_offset)
    phi_t = q*tp
    if mirror:
        phi_t = -phi_t
    x = (R_major + r_minor*np.cos(phi_t)) * np.cos(theta)
    y = (R_major + r_minor*np.cos(phi_t)) * np.sin(theta)
    z = r_minor*np.sin(phi_t) + z_offset
    return np.column_stack([x, y, z])


def build_rodin_3phase(
    R_major: float,
    r_minor: float,
    p: int,
    q: int,
    phases: int,
    turns: int,
    points: int,
    separate_families: bool,
    gap: float,
    ccw_start_mode: str,
) -> List[Coil]:
    phases = int(max(1, min(phases, 12)))
    q = int(max(1, q))
    cell_fracs = np.arange(phases, dtype=float) / phases
    z_cw = -gap/2.0 if separate_families else 0.0
    z_ccw = +gap/2.0 if separate_families else 0.0
    theta_offset_ccw = np.pi if str(ccw_start_mode).startswith("Opposite") else 0.0
    colors_cw = ["crimson", "darkorange", "gold", "tomato", "sienna", "khaki"]
    colors_ccw = ["royalblue", "navy", "teal", "deepskyblue", "slateblue", "cyan"]
    coils: List[Coil] = []
    for i, cf in enumerate(cell_fracs):
        pts = torus_knot_cellphase_polyline(R_major, r_minor, p, q, points, turns, cf, False, z_cw, 0.0)
        coils.append((pts, colors_cw[i % len(colors_cw)], "-", f"Rodin CW phase {i+1}", 1.0))
    for i, cf in enumerate(cell_fracs):
        pts = torus_knot_cellphase_polyline(R_major, r_minor, p, q, points, turns, cf, True, z_ccw, theta_offset_ccw)
        coils.append((pts, colors_ccw[i % len(colors_ccw)], "--", f"Rodin CCW phase {i+1}", 1.0))
    return coils


# =============================================================================
# Coil geometry: SawShape and Starship from GUI-SawBowl.py
# =============================================================================
def alternating_skip_indices(S: int, step_fwd: int, step_bwd: int, n_pairs: int, start: int = 1) -> np.ndarray:
    idx = int(start)
    seq = [idx]
    for k in range(2*int(max(1, n_pairs))):
        if k % 2 == 0:
            idx = (idx + int(step_fwd) - 1) % int(S) + 1
        else:
            idx = (idx + int(step_bwd) - 1) % int(S) + 1
        seq.append(idx)
    return np.array(seq, dtype=int)


def r_profile(s: np.ndarray, Rb: float, Rt: float, profile: str, power: float) -> np.ndarray:
    profile = str(profile)
    if profile == "Exponential":
        return Rb + (Rt - Rb) * (s**power)
    if profile == "Inverse Exp":
        return Rt - (Rt - Rb) * (s**power)
    return Rb + (Rt - Rb) * s


def build_sawshape_phase(seq: np.ndarray, S: int, Rb: float, Rt: float, spacing: float,
                         angle_offset: float, profile: str, power: float, curved: bool,
                         samples_per_seg: int) -> np.ndarray:
    slot_angles_base = np.linspace(0, 2*np.pi, int(S), endpoint=False) - np.pi/2.0
    N = len(seq) - 1
    s_nodes = np.linspace(0, 1, N+1)
    r_nodes = r_profile(s_nodes, Rb, Rt, profile, power)
    z_nodes = s_nodes * spacing
    if not curved:
        xyz = np.zeros((N+1, 3), dtype=float)
        for k in range(N+1):
            a = slot_angles_base[int(seq[k])-1] + angle_offset
            xyz[k, 0] = r_nodes[k] * np.cos(a)
            xyz[k, 1] = r_nodes[k] * np.sin(a)
            xyz[k, 2] = z_nodes[k]
        return xyz - np.array([0.0, 0.0, spacing/2.0])

    xs, ys, zs = [], [], []
    samples_per_seg = int(max(2, samples_per_seg))
    for k in range(N):
        i0, i1 = int(seq[k])-1, int(seq[k+1])-1
        a0 = slot_angles_base[i0] + angle_offset
        a1 = slot_angles_base[i1] + angle_offset
        da = (a1 - a0 + np.pi) % (2*np.pi) - np.pi
        a_line = a0 + np.linspace(0, 1, samples_per_seg, endpoint=False) * da
        r_line = np.linspace(r_nodes[k], r_nodes[k+1], samples_per_seg, endpoint=False)
        z_line = np.linspace(z_nodes[k], z_nodes[k+1], samples_per_seg, endpoint=False)
        xs.append(r_line*np.cos(a_line))
        ys.append(r_line*np.sin(a_line))
        zs.append(z_line)
    pts = np.column_stack([np.concatenate(xs), np.concatenate(ys), np.concatenate(zs)])
    return pts - np.array([0.0, 0.0, spacing/2.0])


def build_sawshape(S: int, step_fwd: int, step_bwd: int, n_pairs: int, Rb: float, Rt: float,
                   spacing: float, profile: str, power: float, curved: bool,
                   samples_per_seg: int) -> List[Coil]:
    seq = alternating_skip_indices(S, step_fwd, step_bwd, n_pairs, start=1)
    phase_offsets = [0.0, 2*np.pi/3, 4*np.pi/3]
    colors = ["tab:purple", "tab:blue", "tab:green"]
    labels = ["SawShape phase A", "SawShape phase B", "SawShape phase C"]
    coils: List[Coil] = []
    for ang, col, label in zip(phase_offsets, colors, labels):
        pts = build_sawshape_phase(seq, S, Rb, Rt, spacing, ang, profile, power, curved, samples_per_seg)
        coils.append((pts, col, "-", label, 1.0))
    return coils


STARSHIP_ROT_ANGLE = (2*np.pi/27) / 3
STARSHIP_COIL_ANGLES = (np.linspace(0, 2*np.pi, 28)[:-1] - np.pi*1.5 + (2*np.pi/27))[::-1] + STARSHIP_ROT_ANGLE
STARSHIP_SEGMENT_SHIFT = (2*np.pi/27) / 3


def starship_saw_to_27(saw_seq: np.ndarray, phase_offset_27: int) -> np.ndarray:
    return np.array([((int(s)*3 - int(phase_offset_27) - 1) % 27) + 1 for s in saw_seq], dtype=int)


def build_starship_path(seq_27: np.ndarray, phase_angle: float, segment: int, Rb: float, Rt: float,
                        spacing: float, profile: str, power: float, curved: bool,
                        samples_per_seg: int, reverse: bool = False) -> np.ndarray:
    if reverse:
        seq_27 = seq_27[::-1]
    N = len(seq_27) - 1
    s_nodes = np.linspace(0, 1, N+1)
    r_nodes = r_profile(s_nodes, Rb, Rt, profile, power)
    z_nodes = s_nodes * spacing
    seg = STARSHIP_SEGMENT_SHIFT * (int(segment) - 1)
    if not curved:
        pts = np.zeros((N+1, 3), dtype=float)
        for k in range(N+1):
            a = STARSHIP_COIL_ANGLES[int(seq_27[k])-1] + seg + phase_angle
            pts[k, 0] = r_nodes[k]*np.cos(a)
            pts[k, 1] = r_nodes[k]*np.sin(a)
            pts[k, 2] = z_nodes[k]
        return pts - np.array([0.0, 0.0, spacing/2.0])

    xs, ys, zs = [], [], []
    samples_per_seg = int(max(2, samples_per_seg))
    for k in range(N):
        i0, i1 = int(seq_27[k])-1, int(seq_27[k+1])-1
        a0 = STARSHIP_COIL_ANGLES[i0] + seg + phase_angle
        a1 = STARSHIP_COIL_ANGLES[i1] + seg + phase_angle
        da = (a1 - a0 + np.pi) % (2*np.pi) - np.pi
        a_line = a0 + np.linspace(0, 1, samples_per_seg, endpoint=False)*da
        r_line = np.linspace(r_nodes[k], r_nodes[k+1], samples_per_seg, endpoint=False)
        z_line = np.linspace(z_nodes[k], z_nodes[k+1], samples_per_seg, endpoint=False)
        xs.append(r_line*np.cos(a_line))
        ys.append(r_line*np.sin(a_line))
        zs.append(z_line)
    pts = np.column_stack([np.concatenate(xs), np.concatenate(ys), np.concatenate(zs)])
    return pts - np.array([0.0, 0.0, spacing/2.0])


def build_starship(S: int, step_fwd: int, step_bwd: int, n_pairs: int, Rb: float, Rt: float,
                   spacing: float, profile: str, power: float, curved: bool,
                   samples_per_seg: int, ccw_start_mode: str = "Opposite (180 deg)") -> List[Coil]:
    # Same conceptual mapping as GUI-SawBowl.py: ABC + anti set, each with fwd/neu/bwd strands.
    anti_angle = np.pi if str(ccw_start_mode).startswith("Opposite") else 0.0
    saw_seq = alternating_skip_indices(S, step_fwd, step_bwd, n_pairs, start=1)
    specs = [
        (0, 0.0, False, "A", ["tab:blue", "tab:cyan", "steelblue"]),
        (9, 0.0, False, "B", ["tab:red", "tab:orange", "salmon"]),
        (18, 0.0, False, "C", ["tab:green", "tab:purple", "yellowgreen"]),
        (0, anti_angle, True, "a", ["navy", "deepskyblue", "slateblue"]),
        (9, anti_angle, True, "b", ["maroon", "tomato", "darkorange"]),
        (18, anti_angle, True, "c", ["darkgreen", "limegreen", "olive"]),
    ]
    strands = [(1, "fwd", "-"), (2, "neu", "--"), (3, "bwd", "-")]
    coils: List[Coil] = []
    for phase_off27, phase_angle, reverse, tag, colors in specs:
        seq_27 = starship_saw_to_27(saw_seq, phase_off27)
        for (segment, strand_name, ls), color in zip(strands, colors):
            pts = build_starship_path(seq_27, phase_angle, segment, Rb, Rt, spacing, profile, power,
                                      curved, samples_per_seg, reverse=reverse)
            coils.append((pts, color, ls, f"Starship {tag} {strand_name}", 1.0))
    return coils


# =============================================================================
# Biot-Savart and field helpers
# =============================================================================
def biot_savart_wire_grid_chunked(grid: Grid3D, polyline: np.ndarray, current: float,
                                  r_softening: float, chunk: int = 96) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    X, Y, Z = grid.X, grid.Y, grid.Z
    Bx = np.zeros_like(X, dtype=np.float64)
    By = np.zeros_like(Y, dtype=np.float64)
    Bz = np.zeros_like(Z, dtype=np.float64)

    polyline = finite_polyline(polyline)
    if polyline.shape[0] < 2 or abs(current) < 1e-30:
        return Bx, By, Bz

    p0 = polyline[:-1]
    p1 = polyline[1:]
    dl = p1 - p0
    mid = 0.5 * (p0 + p1)
    target = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
    rs2 = float(max(1e-15, r_softening)) ** 2

    for i0 in range(0, len(dl), int(max(1, chunk))):
        i1 = min(i0 + chunk, len(dl))
        dL = dl[i0:i1]
        M = mid[i0:i1]
        r_vec = target[:, None, :] - M[None, :, :]
        r_sq = np.sum(r_vec*r_vec, axis=2) + rs2
        r_cubed = r_sq * np.sqrt(r_sq)
        cross = np.cross(dL[None, :, :], r_vec)
        factor = (MU0_4PI * current) / r_cubed
        Bseg = cross * factor[:, :, None]
        Bsum = np.sum(Bseg, axis=1)
        Bx += Bsum[:, 0].reshape(X.shape)
        By += Bsum[:, 1].reshape(Y.shape)
        Bz += Bsum[:, 2].reshape(Z.shape)

    return Bx, By, Bz


def estimate_bounds_from_coils(coils: List[Coil], margin: float = 1.45) -> float:
    pts = [finite_polyline(c[0]) for c in coils if finite_polyline(c[0]).shape[0] > 0]
    if not pts:
        return 1.0
    all_pts = np.vstack(pts)
    max_abs = float(np.max(np.abs(all_pts)))
    return max(1e-3, margin * max_abs)


# =============================================================================
# GUI app
# =============================================================================
class RodinGUI3(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("rodin_GUI3 — Rodin + SawShape + Starship coil field GUI")
        self.geometry("1500x900")
        self._after_id = None
        self._layout_heatmap = None
        self._cbar_heat = None
        self._cbar_b = None
        self._cache_key = None
        self._cache: Dict[str, object] = {}
        self._spin_refs: Dict[str, ttk.Spinbox] = {}
        self._entry_refs: Dict[str, ttk.Entry] = {}

        # Main vars
        self.var_quality = tk.StringVar(value="Normal")
        self.var_preset = tk.StringVar(value="Rodin 3-phase CW/CCW")
        self.var_phase_drive = tk.StringVar(value="All +I")

        # Generic controls
        self.var_N = tk.IntVar(value=10)
        self.var_R_m = tk.DoubleVar(value=0.035)
        self.var_L_m = tk.DoubleVar(value=0.090)

        # Rodin controls
        self.var_major_d_cm = tk.DoubleVar(value=9.8)
        self.var_minor_r_mm = tk.DoubleVar(value=12.0)
        self.var_p = tk.IntVar(value=5)
        self.var_q = tk.IntVar(value=12)
        self.var_turns = tk.IntVar(value=1)
        self.var_phases = tk.IntVar(value=3)
        self.var_separate = tk.BooleanVar(value=True)
        self.var_gap_cm = tk.DoubleVar(value=5.0)
        self.var_ccw_start = tk.StringVar(value="Same")
        self.var_starship_ccw_start = tk.StringVar(value="Opposite (180 deg)")

        # Saw/Starship shape controls, in mm
        self.var_shape_Rb_mm = tk.DoubleVar(value=12.0)
        self.var_shape_Rt_mm = tk.DoubleVar(value=28.0)
        self.var_shape_spacing_mm = tk.DoubleVar(value=18.0)
        self.var_shape_layers = tk.IntVar(value=20)
        self.var_shape_power = tk.DoubleVar(value=2.2)
        self.var_shape_profile = tk.StringVar(value="Exponential")
        self.var_saw_S = tk.IntVar(value=40)
        self.var_saw_fwd = tk.IntVar(value=11)
        self.var_saw_bwd = tk.IntVar(value=-9)
        self.var_starship_S = tk.IntVar(value=9)
        self.var_starship_fwd = tk.IntVar(value=4)
        self.var_starship_bwd = tk.IntVar(value=4)
        self.var_samples_per_seg = tk.IntVar(value=24)

        # Compute/viz controls
        self.var_I = tk.DoubleVar(value=1.0)
        self.var_field_backend = tk.StringVar(value="NumPy softened")
        self._sstcore_module = None
        self._sstcore_checked = False
        self.var_bounds_m = tk.DoubleVar(value=0.09)
        self.var_auto_bounds = tk.BooleanVar(value=True)
        self.var_grid_res = tk.IntVar(value=25)
        self.var_poly_pts = tk.IntVar(value=1400)
        self.var_soft_m = tk.DoubleVar(value=0.001)
        self.var_show_quiver = tk.BooleanVar(value=True)
        self.var_show_null = tk.BooleanVar(value=False)
        self.var_show_heatmap = tk.BooleanVar(value=True)
        self.var_null_threshold = tk.DoubleVar(value=0.60)
        self.var_b_floor = tk.DoubleVar(value=1e-12)
        self.var_quiver_step = tk.IntVar(value=2)
        self.var_arrow_scale = tk.DoubleVar(value=0.25)
        self.var_show_legend = tk.BooleanVar(value=False)
        self.var_autoupdate = tk.BooleanVar(value=False)

        self._build_controls()
        self._build_plot()
        self._apply_quality_preset(initial=True)
        self.update_plot()

    # ------------------------------------------------------------------
    # UI construction helpers
    # ------------------------------------------------------------------
    def _quality_map(self):
        return {
            "Low": {"grid_res": 17, "poly_pts": 700, "quiver_step": 3, "samples_per_seg": 12},
            "Normal": {"grid_res": 25, "poly_pts": 1400, "quiver_step": 2, "samples_per_seg": 24},
            "High": {"grid_res": 33, "poly_pts": 2400, "quiver_step": 2, "samples_per_seg": 36},
        }

    def _apply_quality_preset(self, initial=False):
        p = self._quality_map().get(self.var_quality.get(), self._quality_map()["Normal"])
        self.var_grid_res.set(p["grid_res"])
        self.var_poly_pts.set(p["poly_pts"])
        self.var_quiver_step.set(p["quiver_step"])
        self.var_samples_per_seg.set(p["samples_per_seg"])
        if not initial:
            self.lbl_status.config(text=f"Applied quality: {self.var_quality.get()}")

    def _add_labeled_entry(self, parent, label, var, key=None):
        block = ttk.Frame(parent)
        block.pack(fill=tk.X, pady=3)
        ttk.Label(block, text=label).pack(anchor="w")
        e = ttk.Entry(block, textvariable=var)
        e.pack(fill=tk.X)
        if key:
            self._entry_refs[key] = e
        return e

    def _add_labeled_spin(self, parent, label, var, from_, to_, increment=1, key=None):
        block = ttk.Frame(parent)
        block.pack(fill=tk.X, pady=3)
        ttk.Label(block, text=label).pack(anchor="w")
        sp = ttk.Spinbox(block, from_=from_, to=to_, increment=increment, textvariable=var)
        sp.pack(fill=tk.X)
        if key:
            self._spin_refs[key] = sp
        return sp

    def _add_slider(self, parent, label, var, from_, to_, fmt=lambda v: f"{v:.3g}"):
        block = ttk.Frame(parent)
        block.pack(fill=tk.X, pady=5)
        top = ttk.Frame(block)
        top.pack(fill=tk.X)
        ttk.Label(top, text=label).pack(side=tk.LEFT)
        val_lbl = ttk.Label(top, text="")
        val_lbl.pack(side=tk.RIGHT)

        def refresh(*_):
            try:
                val_lbl.configure(text=fmt(float(var.get())))
            except Exception:
                val_lbl.configure(text="?")

        scale = ttk.Scale(block, from_=from_, to=to_, orient="horizontal", variable=var)
        scale.pack(fill=tk.X)
        var.trace_add("write", lambda *_: refresh())
        refresh()
        return scale

    def _build_controls(self):
        sidebar = ttk.Frame(self)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)
        scroll = ScrollableFrame(sidebar, width=500)
        scroll.pack(fill=tk.BOTH, expand=True)
        frm = scroll.inner

        # Quality
        qb = ttk.Frame(frm)
        qb.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(qb, text="Quality preset", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        qrow = ttk.Frame(qb)
        qrow.pack(fill=tk.X, pady=3)
        ttk.Combobox(qrow, textvariable=self.var_quality, values=["Low", "Normal", "High"], state="readonly").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(qrow, text="Apply", command=self._apply_quality_preset).pack(side=tk.RIGHT, padx=(6, 0))
        self.var_quality.trace_add("write", lambda *_: self._apply_quality_preset())

        self.sec_preset = CollapsibleSection(frm, "Coil preset", True); self.sec_preset.pack(fill=tk.X)
        self.sec_generic = CollapsibleSection(frm, "Generic coil controls", False); self.sec_generic.pack(fill=tk.X)
        self.sec_rodin = CollapsibleSection(frm, "Rodin / knot controls", True); self.sec_rodin.pack(fill=tk.X)
        self.sec_shape = CollapsibleSection(frm, "SawShape / Starship shape sliders", True); self.sec_shape.pack(fill=tk.X)
        self.sec_compute = CollapsibleSection(frm, "Compute / field", True); self.sec_compute.pack(fill=tk.X)
        self.sec_viz = CollapsibleSection(frm, "Visual / export", True); self.sec_viz.pack(fill=tk.X)
        sec_preset = self.sec_preset
        sec_generic = self.sec_generic
        sec_rodin = self.sec_rodin
        sec_shape = self.sec_shape
        sec_compute = self.sec_compute
        sec_viz = self.sec_viz

        pbody = sec_preset.body
        ttk.Label(pbody, text="Preset").pack(anchor="w")
        presets = [
            "Solenoide", "Toroid", "Enkele winding", "Helmholtz", "Rodin-knot",
            "Rodin 3-phase CW/CCW",
            "Straight SawShape", "Curved SawShape",
            "Straight Starship", "Curved Starship",
        ]
        ttk.Combobox(pbody, textvariable=self.var_preset, values=presets, state="readonly").pack(fill=tk.X, pady=(0, 6))
        ttk.Label(pbody, text="Phase drive / current assignment").pack(anchor="w")
        ttk.Combobox(pbody, textvariable=self.var_phase_drive,
                     values=["All +I", "ABC static [1,-0.5,-0.5]", "ACB static [1,-0.5,-0.5]"],
                     state="readonly").pack(fill=tk.X)

        g = sec_generic.body
        self._add_labeled_spin(g, "Windingen N", self.var_N, 1, 120, key="N")
        self._add_labeled_entry(g, "Straal R [m]", self.var_R_m, key="R_m")
        self._add_labeled_entry(g, "Lengte/grootte L [m]", self.var_L_m, key="L_m")

        r = sec_rodin.body
        self.frame_knot_common = ttk.Frame(r)
        self.frame_knot_common.pack(fill=tk.X)
        self._add_labeled_spin(self.frame_knot_common, "p", self.var_p, 1, 200, key="p")
        self._add_labeled_spin(self.frame_knot_common, "q", self.var_q, 1, 200, key="q")
        self._add_labeled_spin(self.frame_knot_common, "Turns", self.var_turns, 1, 50, key="turns")

        self.frame_rodin3 = ttk.Frame(r)
        self.frame_rodin3.pack(fill=tk.X)
        self._add_labeled_entry(self.frame_rodin3, "Major diameter [cm]", self.var_major_d_cm, key="major_d_cm")
        self._add_labeled_entry(self.frame_rodin3, "Minor radius [mm]", self.var_minor_r_mm, key="minor_r_mm")
        self._add_labeled_spin(self.frame_rodin3, "Phases per cell", self.var_phases, 1, 12, key="phases")
        ttk.Checkbutton(self.frame_rodin3, text="Separate CW/CCW families along z", variable=self.var_separate).pack(anchor="w", pady=2)
        self._add_slider(self.frame_rodin3, "Gap [cm]", self.var_gap_cm, 0.0, 25.0, lambda v: f"{v:.2f} cm")
        ttk.Label(self.frame_rodin3, text="CCW start relative to CW").pack(anchor="w")
        ttk.Combobox(self.frame_rodin3, textvariable=self.var_ccw_start, values=["Same", "Opposite (1->19)"], state="readonly").pack(fill=tk.X)

        s = sec_shape.body
        self.frame_shape_common = ttk.Frame(s)
        self.frame_shape_common.pack(fill=tk.X)
        self._add_slider(self.frame_shape_common, "R bottom [mm]", self.var_shape_Rb_mm, 1.0, 80.0, lambda v: f"{v:.1f} mm")
        self._add_slider(self.frame_shape_common, "R top [mm]", self.var_shape_Rt_mm, 1.0, 80.0, lambda v: f"{v:.1f} mm")
        self._add_slider(self.frame_shape_common, "Height / spacing [mm]", self.var_shape_spacing_mm, 1.0, 80.0, lambda v: f"{v:.1f} mm")
        self._add_labeled_spin(self.frame_shape_common, "Layers / pairs", self.var_shape_layers, 1, 240, key="shape_layers")
        self._add_slider(self.frame_shape_common, "Bowl power", self.var_shape_power, 0.2, 6.0, lambda v: f"{v:.2f}")
        ttk.Label(self.frame_shape_common, text="Bowl profile").pack(anchor="w")
        ttk.Combobox(self.frame_shape_common, textvariable=self.var_shape_profile, values=["Exponential", "Linear", "Inverse Exp"], state="readonly").pack(fill=tk.X, pady=(0, 6))
        self._add_labeled_spin(self.frame_shape_common, "Samples per segment", self.var_samples_per_seg, 2, 120, key="samples_per_seg")

        self.frame_sawshape = ttk.Frame(s)
        self.frame_sawshape.pack(fill=tk.X)
        ttk.Label(self.frame_sawshape, text="SawShape-specific", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(6, 0))
        self._add_labeled_spin(self.frame_sawshape, "Saw S", self.var_saw_S, 3, 200, key="saw_S")
        self._add_labeled_spin(self.frame_sawshape, "Saw forward step", self.var_saw_fwd, -200, 200, key="saw_fwd")
        self._add_labeled_spin(self.frame_sawshape, "Saw backward step", self.var_saw_bwd, -200, 200, key="saw_bwd")

        self.frame_starship = ttk.Frame(s)
        self.frame_starship.pack(fill=tk.X)
        ttk.Label(self.frame_starship, text="Starship-specific", font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(6, 0))
        self._add_labeled_spin(self.frame_starship, "Starship S", self.var_starship_S, 3, 200, key="starship_S")
        self._add_labeled_spin(self.frame_starship, "Starship forward step", self.var_starship_fwd, -200, 200, key="starship_fwd")
        self._add_labeled_spin(self.frame_starship, "Starship backward step", self.var_starship_bwd, -200, 200, key="starship_bwd")
        ttk.Label(self.frame_starship, text="CCW / anti start relative to CW / ABC").pack(anchor="w")
        ttk.Combobox(self.frame_starship, textvariable=self.var_starship_ccw_start,
                     values=["Same", "Opposite (180 deg)"], state="readonly").pack(fill=tk.X)

        c = sec_compute.body
        self._add_labeled_entry(c, "Current I [A]", self.var_I, key="I")
        ttk.Label(c, text="Field backend").pack(anchor="w")
        ttk.Combobox(
            c,
            textvariable=self.var_field_backend,
            values=["NumPy softened", "Auto SSTcore/NumPy", "SSTcore C++ fast"],
            state="readonly",
        ).pack(fill=tk.X, pady=(0, 6))
        ttk.Checkbutton(c, text="Auto bounds from coil", variable=self.var_auto_bounds).pack(anchor="w", pady=2)
        self._add_labeled_entry(c, "Bounds [m] if Auto off", self.var_bounds_m, key="bounds_m")
        self._add_labeled_spin(c, "Grid resolution", self.var_grid_res, 10, 60, key="grid_res")
        self._add_labeled_spin(c, "Polyline points", self.var_poly_pts, 200, 8000, 50, key="poly_pts")
        self._add_labeled_entry(c, "Softening [m]", self.var_soft_m, key="soft_m")

        v = sec_viz.body
        self._add_labeled_spin(v, "Quiver step", self.var_quiver_step, 1, 10, key="quiver_step")
        self._add_labeled_entry(v, "Arrow scale", self.var_arrow_scale, key="arrow_scale")
        ttk.Checkbutton(v, text="Show quiver", variable=self.var_show_quiver).pack(anchor="w", pady=2)
        ttk.Checkbutton(v, text="Show null proxy scatter 1/|B|", variable=self.var_show_null).pack(anchor="w", pady=2)
        self._add_slider(v, "Null threshold", self.var_null_threshold, 0.0, 0.98, lambda x: f"{x:.2f}")
        self._add_labeled_entry(v, "Null floor B [T]", self.var_b_floor, key="b_floor")
        ttk.Checkbutton(v, text="Show mid-plane heatmap", variable=self.var_show_heatmap).pack(anchor="w", pady=2)
        ttk.Checkbutton(v, text="Show legend", variable=self.var_show_legend).pack(anchor="w", pady=2)
        buttons = ttk.Frame(v); buttons.pack(fill=tk.X, pady=(8, 2))
        ttk.Button(buttons, text="Save PNG", command=self.save_png).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(buttons, text="Export coil CSV", command=self.export_csv).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        bottom = ttk.Frame(frm)
        bottom.pack(fill=tk.X, pady=(10, 8))
        ttk.Button(bottom, text="Update", command=self.update_plot).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Checkbutton(bottom, variable=self.var_autoupdate, text="Auto").pack(side=tk.RIGHT)
        self.lbl_status = ttk.Label(frm, text="Ready.")
        self.lbl_status.pack(anchor="w", pady=(0, 8))
        self._bind_autoupdate()
        self._refresh_option_visibility()


    def _refresh_option_visibility(self):
        """Show only the controls relevant to the currently selected coil preset."""
        preset = str(self.var_preset.get())
        is_generic = preset in ["Solenoide", "Toroid", "Enkele winding", "Helmholtz", "Rodin-knot"]
        is_rodin3 = preset == "Rodin 3-phase CW/CCW"
        is_knot = preset == "Rodin-knot"
        is_saw = "SawShape" in preset
        is_starship = "Starship" in preset
        is_shape = is_saw or is_starship

        # Hide dynamic top-level sections, then reinsert only those needed, in stable order.
        for sec in [self.sec_generic, self.sec_rodin, self.sec_shape]:
            try:
                sec.pack_forget()
            except Exception:
                pass
        if is_generic:
            self.sec_generic.pack(fill=tk.X, before=self.sec_compute)
        if is_rodin3 or is_knot:
            self.sec_rodin.pack(fill=tk.X, before=self.sec_compute)
        if is_shape:
            self.sec_shape.pack(fill=tk.X, before=self.sec_compute)

        # Rodin section internals. Rodin-knot only needs p/q/turns; Rodin 3-phase also needs CW/CCW controls.
        for frame in [self.frame_knot_common, self.frame_rodin3]:
            try:
                frame.pack_forget()
            except Exception:
                pass
        if is_rodin3 or is_knot:
            self.frame_knot_common.pack(fill=tk.X)
        if is_rodin3:
            self.frame_rodin3.pack(fill=tk.X)

        # Shape section internals. Common bowl sliders are shared; Saw/Starship get their own step controls.
        for frame in [self.frame_shape_common, self.frame_sawshape, self.frame_starship]:
            try:
                frame.pack_forget()
            except Exception:
                pass
        if is_shape:
            self.frame_shape_common.pack(fill=tk.X)
        if is_saw:
            self.frame_sawshape.pack(fill=tk.X)
        if is_starship:
            self.frame_starship.pack(fill=tk.X)

    def _build_plot(self):
        plot_frame = ttk.Frame(self)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.fig = plt.Figure(figsize=(10.7, 7.7), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._ensure_axes(self.var_show_heatmap.get())

    def _ensure_axes(self, show_heatmap: bool):
        show_heatmap = bool(show_heatmap)
        if self._layout_heatmap == show_heatmap:
            return
        self.fig.clf()
        self._cbar_heat = None
        self._cbar_b = None
        if show_heatmap:
            self.ax3d = self.fig.add_subplot(1, 2, 1, projection="3d")
            self.ax2d = self.fig.add_subplot(1, 2, 2)
        else:
            self.ax3d = self.fig.add_subplot(1, 1, 1, projection="3d")
            self.ax2d = None
        self._layout_heatmap = show_heatmap

    def _bind_autoupdate(self):
        watch = [
            self.var_quality, self.var_preset, self.var_phase_drive,
            self.var_N, self.var_R_m, self.var_L_m,
            self.var_major_d_cm, self.var_minor_r_mm, self.var_p, self.var_q, self.var_turns, self.var_phases,
            self.var_separate, self.var_gap_cm, self.var_ccw_start, self.var_starship_ccw_start,
            self.var_shape_Rb_mm, self.var_shape_Rt_mm, self.var_shape_spacing_mm, self.var_shape_layers,
            self.var_shape_power, self.var_shape_profile, self.var_saw_S, self.var_saw_fwd, self.var_saw_bwd,
            self.var_starship_S, self.var_starship_fwd, self.var_starship_bwd, self.var_samples_per_seg,
            self.var_I, self.var_field_backend, self.var_bounds_m, self.var_auto_bounds, self.var_grid_res, self.var_poly_pts, self.var_soft_m,
            self.var_show_quiver, self.var_show_null, self.var_show_heatmap, self.var_null_threshold, self.var_b_floor,
            self.var_quiver_step, self.var_arrow_scale, self.var_show_legend,
        ]
        for v in watch:
            v.trace_add("write", lambda *_: self._schedule_update())
        self.var_preset.trace_add("write", lambda *_: self._refresh_option_visibility())

    def _schedule_update(self):
        if not self.var_autoupdate.get():
            return
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        self._after_id = self.after(350, self.update_plot)

    def _commit_inputs(self):
        def to_int(key, var, lo=None, hi=None):
            if key in self._spin_refs:
                try:
                    val = int(float(self._spin_refs[key].get()))
                except Exception:
                    val = int(var.get())
                if lo is not None: val = max(lo, val)
                if hi is not None: val = min(hi, val)
                var.set(val)
        def to_float(key, var, lo=None, hi=None):
            if key in self._entry_refs:
                try:
                    val = float(self._entry_refs[key].get())
                except Exception:
                    val = float(var.get())
                if lo is not None: val = max(lo, val)
                if hi is not None: val = min(hi, val)
                var.set(val)
        for key, var, lo, hi in [
            ("N", self.var_N, 1, 1000), ("p", self.var_p, 1, 500), ("q", self.var_q, 1, 500),
            ("turns", self.var_turns, 1, 200), ("phases", self.var_phases, 1, 12),
            ("shape_layers", self.var_shape_layers, 1, 1000), ("saw_S", self.var_saw_S, 3, 1000),
            ("saw_fwd", self.var_saw_fwd, -1000, 1000), ("saw_bwd", self.var_saw_bwd, -1000, 1000),
            ("starship_S", self.var_starship_S, 3, 1000), ("starship_fwd", self.var_starship_fwd, -1000, 1000),
            ("starship_bwd", self.var_starship_bwd, -1000, 1000), ("samples_per_seg", self.var_samples_per_seg, 2, 240),
            ("grid_res", self.var_grid_res, 10, 80), ("poly_pts", self.var_poly_pts, 200, 10000),
            ("quiver_step", self.var_quiver_step, 1, 20),
        ]:
            to_int(key, var, lo, hi)
        for key, var, lo, hi in [
            ("R_m", self.var_R_m, 1e-6, None), ("L_m", self.var_L_m, 1e-6, None),
            ("major_d_cm", self.var_major_d_cm, 0.1, None), ("minor_r_mm", self.var_minor_r_mm, 0.1, None),
            ("I", self.var_I, None, None), ("bounds_m", self.var_bounds_m, 1e-4, None),
            ("soft_m", self.var_soft_m, 0.0, None), ("b_floor", self.var_b_floor, 0.0, None),
            ("arrow_scale", self.var_arrow_scale, 1e-6, None),
        ]:
            to_float(key, var, lo, hi)

    # ------------------------------------------------------------------
    # Geometry dispatch
    # ------------------------------------------------------------------
    def current_multiplier_for_label(self, label: str, index: int) -> float:
        mode = str(self.var_phase_drive.get())
        if mode == "All +I":
            return 1.0
        phase = 0
        ll = label.lower()
        if "phase b" in ll or " b " in f" {ll} ": phase = 1
        if "phase c" in ll or " c " in f" {ll} ": phase = 2
        if "starship b" in ll or "rodin cw phase 2" in ll or "rodin ccw phase 2" in ll: phase = 1
        if "starship c" in ll or "rodin cw phase 3" in ll or "rodin ccw phase 3" in ll: phase = 2
        abc = [1.0, -0.5, -0.5]
        acb = [1.0, -0.5, -0.5]  # amplitude same; handedness is mostly in wiring/geometry, not static scalar current
        return abc[phase] if mode.startswith("ABC") else acb[phase]

    def build_current_coils(self) -> List[Coil]:
        preset = str(self.var_preset.get())
        poly_pts = int(self.var_poly_pts.get())
        coils: List[Coil]

        if preset in ["Solenoide", "Toroid", "Enkele winding", "Helmholtz", "Rodin-knot"]:
            pts = generic_wire_points(preset, int(self.var_N.get()), float(self.var_R_m.get()), float(self.var_L_m.get()),
                                      poly_pts, int(self.var_p.get()), int(self.var_q.get()), int(self.var_turns.get()))
            coils = [(pts, "darkorange", "-", preset, 1.0)]

        elif preset == "Rodin 3-phase CW/CCW":
            R_major = 0.5 * float(self.var_major_d_cm.get()) * 1e-2
            r_minor = float(self.var_minor_r_mm.get()) * 1e-3
            r_minor = max(1e-6, min(r_minor, 0.95*max(R_major, 1e-9)))
            coils = build_rodin_3phase(
                R_major=R_major,
                r_minor=r_minor,
                p=int(self.var_p.get()),
                q=int(self.var_q.get()),
                phases=int(self.var_phases.get()),
                turns=int(self.var_turns.get()),
                points=poly_pts,
                separate_families=bool(self.var_separate.get()),
                gap=float(self.var_gap_cm.get()) * 1e-2,
                ccw_start_mode=str(self.var_ccw_start.get()),
            )

        elif "SawShape" in preset:
            coils = build_sawshape(
                S=int(self.var_saw_S.get()),
                step_fwd=int(self.var_saw_fwd.get()),
                step_bwd=int(self.var_saw_bwd.get()),
                n_pairs=int(self.var_shape_layers.get()),
                Rb=float(self.var_shape_Rb_mm.get())*1e-3,
                Rt=float(self.var_shape_Rt_mm.get())*1e-3,
                spacing=float(self.var_shape_spacing_mm.get())*1e-3,
                profile=str(self.var_shape_profile.get()),
                power=float(self.var_shape_power.get()),
                curved=preset.startswith("Curved"),
                samples_per_seg=int(self.var_samples_per_seg.get()),
            )

        elif "Starship" in preset:
            coils = build_starship(
                S=int(self.var_starship_S.get()),
                step_fwd=int(self.var_starship_fwd.get()),
                step_bwd=int(self.var_starship_bwd.get()),
                n_pairs=int(self.var_shape_layers.get()),
                Rb=float(self.var_shape_Rb_mm.get())*1e-3,
                Rt=float(self.var_shape_Rt_mm.get())*1e-3,
                spacing=float(self.var_shape_spacing_mm.get())*1e-3,
                profile=str(self.var_shape_profile.get()),
                power=float(self.var_shape_power.get()),
                curved=preset.startswith("Curved"),
                samples_per_seg=int(self.var_samples_per_seg.get()),
                ccw_start_mode=str(self.var_starship_ccw_start.get()),
            )
        else:
            pts = generic_wire_points("Solenoide", 10, 0.035, 0.09, poly_pts, 5, 12, 1)
            coils = [(pts, "darkorange", "-", "Solenoide", 1.0)]

        # Apply static drive multipliers after labels exist
        out = []
        for i, (pts, color, ls, label, _cmul) in enumerate(coils):
            out.append((finite_polyline(pts), color, ls, label, self.current_multiplier_for_label(label, i)))
        return out

    # ------------------------------------------------------------------
    # Render / compute
    # ------------------------------------------------------------------
    def update_plot(self):
        self.lbl_status.config(text="Computing…")
        self.update_idletasks()
        self._commit_inputs()
        show_heatmap = bool(self.var_show_heatmap.get())
        self._ensure_axes(show_heatmap)

        coils = self.build_current_coils()
        I = float(self.var_I.get())
        bounds = estimate_bounds_from_coils(coils) if bool(self.var_auto_bounds.get()) else float(self.var_bounds_m.get())
        res = int(self.var_grid_res.get())
        soft = float(self.var_soft_m.get())
        qstep = int(self.var_quiver_step.get())
        arrow_scale = float(self.var_arrow_scale.get())

        backend_request = str(self.var_field_backend.get())
        sstcore_module = None
        use_sstcore = False
        backend_note = "NumPy softened"
        if backend_request != "NumPy softened":
            if not self._sstcore_checked:
                self._sstcore_module = try_import_sstcore()
                self._sstcore_checked = True
            sstcore_module = self._sstcore_module
            use_sstcore = sstcore_module is not None and hasattr(sstcore_module, "biot_savart_wire_grid")
            if backend_request == "SSTcore C++ fast" and not use_sstcore:
                messagebox.showwarning(
                    "SSTcore not available",
                    "SSTcore/sstcore with biot_savart_wire_grid was not found. Falling back to NumPy."
                )
            if use_sstcore:
                backend_note = f"SSTcore C++ ({getattr(sstcore_module, '__name__', 'sstcore')}; no GUI softening)"

        # cache key includes geometry arrays sampled by shape labels/lengths, not entire arrays
        lens_key = tuple((label, len(pts), tuple(np.round(pts[0], 9)) if len(pts) else None, tuple(np.round(pts[-1], 9)) if len(pts) else None, round(cmul, 6))
                         for pts, _c, _ls, label, cmul in coils)
        compute_key = (str(self.var_preset.get()), lens_key, round(I, 9), round(bounds, 9), res, round(soft, 12), backend_note)
        recompute = compute_key != self._cache_key

        if recompute:
            grid = make_grid(bounds, res)
            Bx = np.zeros_like(grid.X)
            By = np.zeros_like(grid.X)
            Bz = np.zeros_like(grid.X)
            for pts, _color, _ls, label, cmul in coils:
                if use_sstcore:
                    try:
                        bx, by, bz = biot_savart_wire_grid_sstcore(sstcore_module, grid, pts, current=I*cmul)
                    except Exception as exc:
                        backend_note = f"NumPy fallback after SSTcore error: {type(exc).__name__}"
                        bx, by, bz = biot_savart_wire_grid_chunked(grid, pts, current=I*cmul, r_softening=soft, chunk=96)
                        use_sstcore = False
                else:
                    bx, by, bz = biot_savart_wire_grid_chunked(grid, pts, current=I*cmul, r_softening=soft, chunk=96)
                Bx += bx; By += by; Bz += bz
            Bmag = np.sqrt(Bx*Bx + By*By + Bz*Bz) + 1e-30
            self._cache_key = compute_key
            self._cache = dict(grid=grid, Bx=Bx, By=By, Bz=Bz, Bmag=Bmag, bounds=bounds, backend_note=backend_note)
        else:
            grid = self._cache["grid"]
            Bx = self._cache["Bx"]
            By = self._cache["By"]
            Bz = self._cache["Bz"]
            Bmag = self._cache["Bmag"]
            backend_note = self._cache.get("backend_note", backend_note)

        self.ax3d.cla()
        if self.ax2d is not None:
            self.ax2d.cla()

        self.ax3d.set_xlabel("X [m]")
        self.ax3d.set_ylabel("Y [m]")
        self.ax3d.set_zlabel("Z [m]")
        self.ax3d.set_xlim(-bounds, bounds)
        self.ax3d.set_ylim(-bounds, bounds)
        self.ax3d.set_zlim(-bounds, bounds)
        self.ax3d.set_box_aspect((1, 1, 1))

        for pts, color, ls, label, cmul in coils:
            if len(pts) >= 2:
                self.ax3d.plot(pts[:, 0], pts[:, 1], pts[:, 2], color=color, linestyle=ls, lw=1.45, alpha=0.92,
                               label=f"{label} ×{cmul:g}")

        # Null proxy scatter: same idea as rodin_GUI.py, plotting normalized 1/|B| regions.
        if bool(self.var_show_null.get()):
            b_floor = max(0.0, float(self.var_b_floor.get()))
            null_map = 1.0 / (Bmag + b_floor + 1e-300)
            null_map = null_map / max(float(np.nanmax(null_map)), 1e-300)
            mask = null_map > float(self.var_null_threshold.get())
            if np.any(mask):
                idx = np.flatnonzero(mask.ravel())
                max_pts = 6500
                if idx.size > max_pts:
                    idx = idx[np.linspace(0, idx.size - 1, max_pts).astype(int)]
                xf = grid.X.ravel()[idx]
                yf = grid.Y.ravel()[idx]
                zf = grid.Z.ravel()[idx]
                cf = null_map.ravel()[idx]
                self.ax3d.scatter(xf, yf, zf, c=cf, cmap="inferno", s=9, alpha=0.24)

        # Quiver with length scaled to field strength but clipped.
        bclip = float(np.percentile(Bmag, 95)) if np.any(np.isfinite(Bmag)) else 1.0
        bclip = max(bclip, 1e-30)
        bnorm = Normalize(vmin=0.0, vmax=bclip)
        if bool(self.var_show_quiver.get()):
            st = max(1, qstep)
            xs = grid.X[::st, ::st, ::st]
            ys = grid.Y[::st, ::st, ::st]
            zs = grid.Z[::st, ::st, ::st]
            bxs = Bx[::st, ::st, ::st]
            bys = By[::st, ::st, ::st]
            bzs = Bz[::st, ::st, ::st]
            rgba = plt.cm.Blues(bnorm(np.sqrt(bxs*bxs + bys*bys + bzs*bzs))).reshape(-1, 4)
            scale = arrow_scale / bclip
            try:
                self.ax3d.quiver(xs.ravel(), ys.ravel(), zs.ravel(),
                                  (bxs*scale).ravel(), (bys*scale).ravel(), (bzs*scale).ravel(),
                                  length=1.0, normalize=False, color=rgba, alpha=0.55, linewidth=0.25)
            except Exception:
                self.ax3d.quiver(xs, ys, zs, bxs, bys, bzs, length=arrow_scale, normalize=True, alpha=0.35, color="gray")

        if self.ax2d is not None:
            k0 = int(np.argmin(np.abs(grid.z - 0.0)))
            Bmid = Bmag[:, :, k0]
            im = self.ax2d.imshow(np.log10(Bmid.T + 1e-30), origin="lower",
                                  extent=[-bounds, bounds, -bounds, bounds], aspect="equal", cmap="viridis")
            self.ax2d.set_title("Mid-plane z≈0: log10(|B| [T])")
            self.ax2d.set_xlabel("X [m]")
            self.ax2d.set_ylabel("Y [m]")
            self.fig.colorbar(im, ax=self.ax2d, fraction=0.046, pad=0.04)

        sm = ScalarMappable(norm=bnorm, cmap=plt.cm.Blues)
        sm.set_array([])
        self.fig.colorbar(sm, ax=self.ax3d, fraction=0.035, pad=0.02).set_label("|B| [T], clipped p95")

        if bool(self.var_show_legend.get()):
            self.ax3d.legend(loc="upper left", fontsize=7)

        self.ax3d.view_init(elev=22, azim=42)
        self.fig.suptitle(
            f"{self.var_preset.get()} | drive={self.var_phase_drive.get()} | I={I:g} A | bounds={bounds:.3g} m | "
            f"res={res} | backend={backend_note} | cache={'MISS' if recompute else 'HIT'}",
            fontsize=10,
        )
        self.fig.tight_layout(rect=[0, 0, 1, 0.95])
        self.canvas.draw()
        self.lbl_status.config(text=f"Done. Coils={len(coils)}, grid={res}³, bounds={bounds:.4g} m.")

    # ------------------------------------------------------------------
    # Export functions
    # ------------------------------------------------------------------
    def save_png(self):
        fn = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG image", "*.png")],
                                          initialfile="rodin_GUI3_view.png")
        if not fn:
            return
        self.fig.savefig(fn, dpi=180, bbox_inches="tight")
        self.lbl_status.config(text=f"Saved PNG: {fn}")

    def export_csv(self):
        fn = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV file", "*.csv")],
                                          initialfile="rodin_GUI3_coils.csv")
        if not fn:
            return
        coils = self.build_current_coils()
        with open(fn, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["lane", "point_index", "x", "y", "z", "current_multiplier"])
            for pts, _color, _ls, label, cmul in coils:
                for i, p in enumerate(pts):
                    w.writerow([label, i, f"{p[0]:.12g}", f"{p[1]:.12g}", f"{p[2]:.12g}", f"{cmul:.12g}"])
        self.lbl_status.config(text=f"Exported CSV: {fn}")


def main():
    app = RodinGUI3()
    app.mainloop()


if __name__ == "__main__":
    main()
