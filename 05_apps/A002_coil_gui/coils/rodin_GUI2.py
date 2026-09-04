import numpy as np
import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

MU0_4PI = 1e-7  # μ0/(4π)


# ----------------------------
# Scrollable sidebar frame
# ----------------------------
class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, width=430):
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
        delta = int(-1 * (event.delta / 120))
        self.canvas.yview_scroll(delta, "units")

    def _on_mousewheel_linux(self, event):
        self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")


# ----------------------------
# Collapsible section widget
# ----------------------------
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


# ----------------------------
# Grid + interpolation
# ----------------------------
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


def trilinear_interp_vector(grid: Grid3D, Vx, Vy, Vz, p):
    x, y, z = p
    if x < grid.x[0] or x > grid.x[-1] or y < grid.y[0] or y > grid.y[-1] or z < grid.z[0] or z > grid.z[-1]:
        return None

    ix = int(np.clip(np.searchsorted(grid.x, x) - 1, 0, len(grid.x) - 2))
    iy = int(np.clip(np.searchsorted(grid.y, y) - 1, 0, len(grid.y) - 2))
    iz = int(np.clip(np.searchsorted(grid.z, z) - 1, 0, len(grid.z) - 2))

    x0, x1 = grid.x[ix], grid.x[ix + 1]
    y0, y1 = grid.y[iy], grid.y[iy + 1]
    z0, z1 = grid.z[iz], grid.z[iz + 1]

    tx = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
    ty = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
    tz = 0.0 if z1 == z0 else (z - z0) / (z1 - z0)

    def lerp(a, b, t): return a*(1-t) + b*t

    def interp_scalar(F):
        c000 = F[ix,     iy,     iz]
        c100 = F[ix + 1, iy,     iz]
        c010 = F[ix,     iy + 1, iz]
        c110 = F[ix + 1, iy + 1, iz]
        c001 = F[ix,     iy,     iz + 1]
        c101 = F[ix + 1, iy,     iz + 1]
        c011 = F[ix,     iy + 1, iz + 1]
        c111 = F[ix + 1, iy + 1, iz + 1]

        c00 = lerp(c000, c100, tx)
        c10 = lerp(c010, c110, tx)
        c01 = lerp(c001, c101, tx)
        c11 = lerp(c011, c111, tx)
        c0 = lerp(c00, c10, ty)
        c1 = lerp(c01, c11, ty)
        return lerp(c0, c1, tz)

    return np.array([interp_scalar(Vx), interp_scalar(Vy), interp_scalar(Vz)], dtype=float)


def integrate_fieldline(grid: Grid3D, Vx, Vy, Vz, seed, ds=0.22, n_steps=140, direction=+1):
    pts = [np.array(seed, dtype=float)]
    p = np.array(seed, dtype=float)

    for _ in range(n_steps):
        v1 = trilinear_interp_vector(grid, Vx, Vy, Vz, p)
        if v1 is None:
            break
        n1 = np.linalg.norm(v1)
        if n1 < 1e-16:
            break
        k1 = direction * ds * (v1 / n1)

        v2 = trilinear_interp_vector(grid, Vx, Vy, Vz, p + 0.5 * k1)
        if v2 is None:
            break
        n2 = np.linalg.norm(v2)
        if n2 < 1e-16:
            break
        k2 = direction * ds * (v2 / n2)

        v3 = trilinear_interp_vector(grid, Vx, Vy, Vz, p + 0.5 * k2)
        if v3 is None:
            break
        n3 = np.linalg.norm(v3)
        if n3 < 1e-16:
            break
        k3 = direction * ds * (v3 / n3)

        v4 = trilinear_interp_vector(grid, Vx, Vy, Vz, p + k3)
        if v4 is None:
            break
        n4 = np.linalg.norm(v4)
        if n4 < 1e-16:
            break
        k4 = direction * ds * (v4 / n4)

        p = p + (k1 + 2*k2 + 2*k3 + k4) / 6.0
        pts.append(p.copy())

    return np.array(pts)


# ----------------------------
# Coil geometries
# ----------------------------
def torus_knot_polyline(R_major: float, r_minor: float, p: int, q: int, turns: int, n_points: int, mirror: bool = False):
    """
    Simple torus-knot polyline (Rodin-like families can be built from variants,
    but here we provide a single knot path as a "Rodin-knot" option).
    """
    p = int(max(1, p))
    q = int(max(1, q))
    turns = int(max(1, turns))
    n_points = int(max(300, n_points))

    t = np.linspace(0.0, 2.0*np.pi*turns, n_points, endpoint=True)
    theta = p * t
    phi = q * t
    if mirror:
        phi = -phi

    x = (R_major + r_minor*np.cos(phi)) * np.cos(theta)
    y = (R_major + r_minor*np.cos(phi)) * np.sin(theta)
    z = r_minor*np.sin(phi)
    return np.column_stack([x, y, z])


def wire_points(kind: str, N: int, R: float, L: float, pts: int, p_knot: int, q_knot: int, turns_knot: int):
    k = kind.lower()
    pts = int(max(200, pts))

    if k == "enkele winding":
        t = np.linspace(0, 2*np.pi, pts, endpoint=True)
        x = R*np.cos(t); y = R*np.sin(t); z = 0*t
        return np.column_stack([x, y, z])

    if k == "helmholtz":
        sep = np.clip(L/4.0, 0.2*R, 1.6*R)
        t = np.linspace(0, 2*np.pi, pts//2, endpoint=True)
        x = R*np.cos(t); y = R*np.sin(t)
        p1 = np.column_stack([x, y, np.full_like(t, -sep/2)])
        p2 = np.column_stack([x, y, np.full_like(t, +sep/2)])
        return np.vstack([p1, p2])

    if k == "toroid":
        r = R
        a = max(1.5*r, 0.6*L)  # major radius from L
        u = np.linspace(0, 2*np.pi, pts, endpoint=True)  # around major
        v = N*u  # N windings around minor
        x = (a + r*np.cos(v)) * np.cos(u)
        y = (a + r*np.cos(v)) * np.sin(u)
        z = r*np.sin(v)
        return np.column_stack([x, y, z])

    if k == "rodin-knot":
        # Interpret:
        #   R = minor radius, L = controls major radius (like toroid)
        r_minor = max(1e-6, R)
        R_major = max(1.5*r_minor, 0.6*L)
        return torus_knot_polyline(R_major=R_major, r_minor=r_minor, p=p_knot, q=q_knot, turns=turns_knot, n_points=pts)

    # default: solenoïde
    pts_per_turn = max(60, pts // max(1, N))
    t = np.linspace(0, 2*np.pi*N, N*pts_per_turn, endpoint=True)
    z = np.linspace(-L/2, L/2, N*pts_per_turn, endpoint=True)
    x = R*np.cos(t); y = R*np.sin(t)
    return np.column_stack([x, y, z])


# ----------------------------
# Biot–Savart on grid from wire (chunked)
# ----------------------------
def biot_savart_wire_grid_chunked(grid: Grid3D, polyline: np.ndarray, current: float, r_softening: float, chunk=96):
    X, Y, Z = grid.X, grid.Y, grid.Z
    Bx = np.zeros_like(X, dtype=np.float64)
    By = np.zeros_like(Y, dtype=np.float64)
    Bz = np.zeros_like(Z, dtype=np.float64)

    if polyline.shape[0] < 2:
        return Bx, By, Bz

    p0 = polyline[:-1]
    p1 = polyline[1:]
    dl = (p1 - p0)                      # (S,3)
    mid = 0.5 * (p0 + p1)               # (S,3)

    target = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)  # (P,3)
    rs2 = float(r_softening)**2

    for i0 in range(0, len(dl), chunk):
        i1 = min(i0 + chunk, len(dl))
        dL = dl[i0:i1]        # (C,3)
        M = mid[i0:i1]        # (C,3)

        r_vec = target[:, None, :] - M[None, :, :]  # (P,C,3)
        r_sq = np.sum(r_vec*r_vec, axis=2) + rs2    # (P,C)
        r_cubed = r_sq * np.sqrt(r_sq)

        cross = np.cross(dL[None, :, :], r_vec)     # (P,C,3)
        factor = (MU0_4PI * current) / r_cubed      # (P,C)
        Bseg = cross * factor[:, :, None]           # (P,C,3)

        Bsum = np.sum(Bseg, axis=1)                 # (P,3)
        Bx += Bsum[:, 0].reshape(X.shape)
        By += Bsum[:, 1].reshape(Y.shape)
        Bz += Bsum[:, 2].reshape(Z.shape)

    return Bx, By, Bz


# ----------------------------
# Simple induced E (didactic): circles around z
# ----------------------------
def induced_E_about_z(grid: Grid3D, dIdt: float, scale: float):
    X, Y = grid.X, grid.Y
    r = np.sqrt(X*X + Y*Y) + 1e-12
    k = 1e-7 * scale
    Ephi = -k * dIdt * (r / (1.0 + r*r))
    Ex = Ephi * (-Y / r)
    Ey = Ephi * ( X / r)
    Ez = np.zeros_like(Ex)
    return Ex, Ey, Ez


def draw_E_circles(ax3d, R: float, zlim: float):
    zs = np.linspace(-0.6*zlim, 0.6*zlim, 5)
    rs = [0.5*R, 1.0*R, 1.6*R, 2.3*R]
    t = np.linspace(0, 2*np.pi, 220)
    for z in zs:
        for r in rs:
            x = r*np.cos(t); y = r*np.sin(t); zz = np.full_like(t, z)
            ax3d.plot(x, y, zz, color="crimson", alpha=0.35, linewidth=1.0)


# ----------------------------
# Seed presets per coil type (C)
# ----------------------------
def build_seeds(kind: str, R: float, L: float):
    k = kind.lower()
    seeds = []

    if k == "toroid" or k == "rodin-knot":
        # For torus-like shapes: seed around a ring in xy-plane and a few z-levels
        r_minor = max(1e-6, R)
        a = max(1.5*r_minor, 0.6*L)
        for zz in [0.0, 0.5*r_minor, -0.5*r_minor]:
            for ang in np.linspace(0, 2*np.pi, 12, endpoint=False):
                rr = a
                seeds.append((rr*np.cos(ang), rr*np.sin(ang), zz))
            for ang in np.linspace(0, 2*np.pi, 10, endpoint=False):
                rr = a + 0.9*r_minor
                seeds.append((rr*np.cos(ang), rr*np.sin(ang), 0.0))
        return seeds

    if k == "enkele winding":
        # Seed inside loop + outside ring
        for rr in [0.3*R, 0.6*R, 0.9*R, 1.4*R, 2.0*R]:
            for ang in np.linspace(0, 2*np.pi, 10, endpoint=False):
                seeds.append((rr*np.cos(ang), rr*np.sin(ang), 0.0))
        for zz in [-1.0*R, 1.0*R]:
            for rr in [0.6*R, 1.2*R]:
                for ang in np.linspace(0, 2*np.pi, 8, endpoint=False):
                    seeds.append((rr*np.cos(ang), rr*np.sin(ang), zz))
        return seeds

    if k == "helmholtz":
        # Seed between coils and around axis
        sep = np.clip(L/4.0, 0.2*R, 1.6*R)
        for zz in np.linspace(-0.5*sep, 0.5*sep, 5):
            for rr in [0.2*R, 0.5*R, 0.8*R, 1.2*R, 1.8*R]:
                for ang in np.linspace(0, 2*np.pi, 10, endpoint=False):
                    seeds.append((rr*np.cos(ang), rr*np.sin(ang), zz))
        return seeds

    # solenoïde default
    # seed rings along z inside & outside
    for zz in np.linspace(-0.45*L, 0.45*L, 7):
        for rr in [0.2*R, 0.6*R, 0.95*R, 1.4*R, 2.0*R]:
            for ang in np.linspace(0, 2*np.pi, 10, endpoint=False):
                seeds.append((rr*np.cos(ang), rr*np.sin(ang), zz))
    return seeds


# ----------------------------
# GUI
# ----------------------------
class HybridCoilGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Hybrid Coil GUI — Tesla scale + caching + pretty seeds + Rodin-knot")
        self.geometry("1420x860")

        self._after_id = None
        self._layout_heatmap = None
        self._cbar = None

        # Caching (B)
        self._cache_key = None
        self._cache = {}  # stores grid, wire, Bx,By,Bz,Bmag, meta

        # Vars
        self.var_quality = tk.StringVar(value="Normal")

        self.var_kind = tk.StringVar(value="Solenoïde")
        self.var_N = tk.IntVar(value=10)
        self.var_R = tk.DoubleVar(value=1.0)
        self.var_L = tk.DoubleVar(value=8.0)

        # Rodin-knot controls (D)
        self.var_p = tk.IntVar(value=5)
        self.var_q = tk.IntVar(value=12)
        self.var_turns_knot = tk.IntVar(value=1)

        self.var_I = tk.DoubleVar(value=1.0)
        self.var_dIdt = tk.DoubleVar(value=0.0)

        self.var_bounds = tk.DoubleVar(value=6.0)
        self.var_grid_res = tk.IntVar(value=25)
        self.var_poly_pts = tk.IntVar(value=1400)
        self.var_soft = tk.DoubleVar(value=0.01)  # meters

        self.var_show_quiver = tk.BooleanVar(value=True)
        self.var_show_B_lines = tk.BooleanVar(value=True)
        self.var_show_E_lines = tk.BooleanVar(value=True)
        self.var_show_heatmap = tk.BooleanVar(value=True)

        self.var_quiver_step = tk.IntVar(value=2)
        self.var_arrow_scale = tk.DoubleVar(value=0.8)  # visual factor
        self.var_autoupdate = tk.BooleanVar(value=False)

        self.var_n_lines = tk.IntVar(value=28)
        self.var_line_steps = tk.IntVar(value=140)

        # widget refs for commit
        self._spin_refs = {}
        self._entry_refs = {}

        # UI
        self._build_controls()
        self._build_plot()
        self._apply_quality_preset(initial=True)
        self.update_plot()

    # ----------------------------
    # Quality presets
    # ----------------------------
    def _quality_map(self):
        return {
            "Low":    {"grid_res": 17, "poly_pts": 700,  "quiver_step": 3, "n_lines": 16, "line_steps": 90},
            "Normal": {"grid_res": 25, "poly_pts": 1400, "quiver_step": 2, "n_lines": 28, "line_steps": 140},
            "High":   {"grid_res": 33, "poly_pts": 2400, "quiver_step": 2, "n_lines": 44, "line_steps": 190},
        }

    def _apply_quality_preset(self, initial=False):
        preset = self._quality_map().get(self.var_quality.get(), self._quality_map()["Normal"])
        self.var_grid_res.set(preset["grid_res"])
        self.var_poly_pts.set(preset["poly_pts"])
        self.var_quiver_step.set(preset["quiver_step"])
        self.var_n_lines.set(preset["n_lines"])
        self.var_line_steps.set(preset["line_steps"])
        if not initial:
            self.lbl_status.config(text=f"Applied quality: {self.var_quality.get()}")

    def _on_quality_change(self, *_):
        self._apply_quality_preset()
        if self.var_autoupdate.get():
            self._schedule_update()

    # ----------------------------
    # Build plot area
    # ----------------------------
    def _build_plot(self):
        plot_frame = ttk.Frame(self)
        plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.fig = plt.Figure(figsize=(10.2, 7.3), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self._ensure_axes(self.var_show_heatmap.get())

    def _ensure_axes(self, show_heatmap: bool):
        show_heatmap = bool(show_heatmap)
        if self._layout_heatmap == show_heatmap:
            return

        if self._cbar is not None:
            try:
                self._cbar.remove()
            except Exception:
                pass
            self._cbar = None

        self.fig.clf()
        if show_heatmap:
            self.ax3d = self.fig.add_subplot(1, 2, 1, projection="3d")
            self.ax2d = self.fig.add_subplot(1, 2, 2)
        else:
            self.ax3d = self.fig.add_subplot(1, 1, 1, projection="3d")
            self.ax2d = None

        self._layout_heatmap = show_heatmap

    # ----------------------------
    # Sidebar controls
    # ----------------------------
    def _build_controls(self):
        sidebar = ttk.Frame(self)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)

        scroll = ScrollableFrame(sidebar, width=480)
        scroll.pack(fill=tk.BOTH, expand=True)
        frm = scroll.inner

        # Quality
        qb = ttk.Frame(frm); qb.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(qb, text="Quality preset", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        qrow = ttk.Frame(qb); qrow.pack(fill=tk.X, pady=3)
        ttk.Combobox(qrow, textvariable=self.var_quality, values=["Low", "Normal", "High"], state="readonly") \
            .pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(qrow, text="Apply", command=self._apply_quality_preset).pack(side=tk.RIGHT, padx=(6, 0))
        self.var_quality.trace_add("write", self._on_quality_change)

        sec_coil = CollapsibleSection(frm, "Coil type + geometry", True); sec_coil.pack(fill=tk.X)
        sec_rodin = CollapsibleSection(frm, "Rodin-knot params (only used for Rodin-knot)", False); sec_rodin.pack(fill=tk.X)
        sec_compute = CollapsibleSection(frm, "Compute", True); sec_compute.pack(fill=tk.X)
        sec_viz = CollapsibleSection(frm, "Viz", True); sec_viz.pack(fill=tk.X)

        c = sec_coil.body
        ttk.Label(c, text="Spoeltype").pack(anchor="w")
        ttk.Combobox(c, textvariable=self.var_kind,
                     values=["Solenoïde", "Toroid", "Enkele winding", "Helmholtz", "Rodin-knot"],
                     state="readonly").pack(fill=tk.X, pady=(0, 6))

        self._add_labeled_spin(c, "Windingen (N)", self.var_N, 1, 60, 1, key="N")
        self._add_labeled_entry(c, "Straal R [m]", self.var_R, key="R")
        self._add_labeled_entry(c, "Lengte/grootte L [m]", self.var_L, key="L")

        rsec = sec_rodin.body
        self._add_labeled_spin(rsec, "p (knot)", self.var_p, 1, 200, 1, key="p")
        self._add_labeled_spin(rsec, "q (knot)", self.var_q, 1, 200, 1, key="q")
        self._add_labeled_spin(rsec, "turns (knot)", self.var_turns_knot, 1, 30, 1, key="turns_knot")

        comp = sec_compute.body
        self._add_labeled_entry(comp, "Stroom I [A]", self.var_I, key="I")
        self._add_labeled_entry(comp, "dI/dt [A/s] (voor E)", self.var_dIdt, key="dIdt")
        self._add_labeled_entry(comp, "Bounds [m]", self.var_bounds, key="bounds")
        self._add_labeled_spin(comp, "Grid resolution", self.var_grid_res, 10, 55, 1, key="grid_res")
        self._add_labeled_spin(comp, "Polyline points", self.var_poly_pts, 200, 6000, 50, key="poly_pts")
        self._add_labeled_entry(comp, "Softening [m]", self.var_soft, key="soft")

        v = sec_viz.body
        self._add_labeled_spin(v, "Quiver step", self.var_quiver_step, 1, 10, 1, key="quiver_step")
        self._add_labeled_entry(v, "Arrow scale (visual)", self.var_arrow_scale, key="arrow_scale")
        self._add_labeled_spin(v, "Aantal B-veldlijnen", self.var_n_lines, 0, 160, 1, key="n_lines")
        self._add_labeled_spin(v, "Veldlijn steps", self.var_line_steps, 20, 500, 10, key="line_steps")

        ttk.Checkbutton(v, variable=self.var_show_quiver, text="Toon B/E pijlen (lengte=sterkte)").pack(anchor="w", pady=2)
        ttk.Checkbutton(v, variable=self.var_show_B_lines, text="Toon B-veldlijnen").pack(anchor="w", pady=2)
        ttk.Checkbutton(v, variable=self.var_show_E_lines, text="Toon E-veldlijnen (cirkels)").pack(anchor="w", pady=2)
        ttk.Checkbutton(v, variable=self.var_show_heatmap, text="Toon |B| heatmap (z≈0)").pack(anchor="w", pady=2)

        bottom = ttk.Frame(frm); bottom.pack(fill=tk.X, pady=(10, 8))
        ttk.Button(bottom, text="Update", command=self.update_plot).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Checkbutton(bottom, variable=self.var_autoupdate, text="Auto").pack(side=tk.RIGHT)

        self.lbl_status = ttk.Label(frm, text="Ready.")
        self.lbl_status.pack(anchor="w", pady=(0, 8))

        self._bind_autoupdate()

    def _add_labeled_entry(self, parent, label, var, key=None):
        block = ttk.Frame(parent); block.pack(fill=tk.X, pady=3)
        ttk.Label(block, text=label).pack(anchor="w")
        e = ttk.Entry(block, textvariable=var)
        e.pack(fill=tk.X)
        if key is not None:
            self._entry_refs[key] = e
        return e

    def _add_labeled_spin(self, parent, label, var, from_, to_, increment=1, key=None):
        block = ttk.Frame(parent); block.pack(fill=tk.X, pady=3)
        ttk.Label(block, text=label).pack(anchor="w")
        sp = ttk.Spinbox(block, from_=from_, to=to_, increment=increment, textvariable=var)
        sp.pack(fill=tk.X)
        if key is not None:
            self._spin_refs[key] = sp
        return sp

    def _bind_autoupdate(self):
        watch = [
            self.var_quality,
            self.var_kind, self.var_N, self.var_R, self.var_L,
            self.var_p, self.var_q, self.var_turns_knot,
            self.var_I, self.var_dIdt,
            self.var_bounds, self.var_grid_res, self.var_poly_pts, self.var_soft,
            self.var_quiver_step, self.var_arrow_scale, self.var_n_lines, self.var_line_steps,
            self.var_show_quiver, self.var_show_B_lines, self.var_show_E_lines, self.var_show_heatmap,
        ]
        for v in watch:
            v.trace_add("write", lambda *_: self._schedule_update())

    def _schedule_update(self):
        if not self.var_autoupdate.get():
            return
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        self._after_id = self.after(250, self.update_plot)

    def _commit_inputs(self):
        def _safe_int(widget, fallback):
            try:
                return int(float(widget.get()))
            except Exception:
                return fallback

        def _safe_float(widget, fallback):
            try:
                return float(widget.get())
            except Exception:
                return fallback

        # spin
        for k in ["N", "grid_res", "poly_pts", "quiver_step", "n_lines", "line_steps", "p", "q", "turns_knot"]:
            if k in self._spin_refs:
                cur = int(getattr(self, f"var_{k}" if k not in ["turns_knot"] else "var_turns_knot").get())
                val = _safe_int(self._spin_refs[k], cur)
                if k == "N": self.var_N.set(max(1, val))
                elif k == "grid_res": self.var_grid_res.set(max(10, val))
                elif k == "poly_pts": self.var_poly_pts.set(max(200, val))
                elif k == "quiver_step": self.var_quiver_step.set(max(1, val))
                elif k == "n_lines": self.var_n_lines.set(max(0, val))
                elif k == "line_steps": self.var_line_steps.set(max(20, val))
                elif k == "p": self.var_p.set(max(1, val))
                elif k == "q": self.var_q.set(max(1, val))
                elif k == "turns_knot": self.var_turns_knot.set(max(1, val))

        # entry
        if "R" in self._entry_refs: self.var_R.set(max(1e-6, _safe_float(self._entry_refs["R"], float(self.var_R.get()))))
        if "L" in self._entry_refs: self.var_L.set(max(1e-6, _safe_float(self._entry_refs["L"], float(self.var_L.get()))))
        if "I" in self._entry_refs: self.var_I.set(_safe_float(self._entry_refs["I"], float(self.var_I.get())))
        if "dIdt" in self._entry_refs: self.var_dIdt.set(_safe_float(self._entry_refs["dIdt"], float(self.var_dIdt.get())))
        if "bounds" in self._entry_refs: self.var_bounds.set(max(0.2, _safe_float(self._entry_refs["bounds"], float(self.var_bounds.get()))))
        if "soft" in self._entry_refs: self.var_soft.set(max(0.0, _safe_float(self._entry_refs["soft"], float(self.var_soft.get()))))
        if "arrow_scale" in self._entry_refs: self.var_arrow_scale.set(max(1e-3, _safe_float(self._entry_refs["arrow_scale"], float(self.var_arrow_scale.get()))))

    # ----------------------------
    # Compute + render with caching (B)
    # ----------------------------
    def update_plot(self):
        self.lbl_status.config(text="Computing…")
        self.update_idletasks()

        self._commit_inputs()

        kind = str(self.var_kind.get())
        N = int(self.var_N.get())
        R = float(self.var_R.get())
        L = float(self.var_L.get())
        p_knot = int(self.var_p.get())
        q_knot = int(self.var_q.get())
        turns_knot = int(self.var_turns_knot.get())

        I = float(self.var_I.get())
        dIdt = float(self.var_dIdt.get())

        bounds = float(self.var_bounds.get())
        res = int(self.var_grid_res.get())
        poly_pts = int(self.var_poly_pts.get())
        soft = float(self.var_soft.get())

        show_quiver = bool(self.var_show_quiver.get())
        show_B_lines = bool(self.var_show_B_lines.get())
        show_E_lines = bool(self.var_show_E_lines.get())
        show_heatmap = bool(self.var_show_heatmap.get())

        quiver_step = int(self.var_quiver_step.get())
        arrow_scale = float(self.var_arrow_scale.get())
        n_lines = int(self.var_n_lines.get())
        line_steps = int(self.var_line_steps.get())

        self._ensure_axes(show_heatmap)

        # --- caching key: only recompute B if these change ---
        compute_key = (
            kind, N, R, L, p_knot, q_knot, turns_knot,
            I, bounds, res, poly_pts, float(max(1e-12, soft))
        )

        recompute = (compute_key != self._cache_key)
        if recompute:
            grid = make_grid(bounds=bounds, res=res)
            wire = wire_points(kind, N=N, R=R, L=L, pts=poly_pts, p_knot=p_knot, q_knot=q_knot, turns_knot=turns_knot)
            Bx, By, Bz = biot_savart_wire_grid_chunked(
                grid, wire, current=I, r_softening=max(1e-12, soft), chunk=96
            )
            Bmag = np.sqrt(Bx*Bx + By*By + Bz*Bz) + 1e-18

            self._cache_key = compute_key
            self._cache = dict(grid=grid, wire=wire, Bx=Bx, By=By, Bz=Bz, Bmag=Bmag)
        else:
            grid = self._cache["grid"]
            wire = self._cache["wire"]
            Bx = self._cache["Bx"]
            By = self._cache["By"]
            Bz = self._cache["Bz"]
            Bmag = self._cache["Bmag"]

        # E field (didactic): computed every time (cheap)
        Ex, Ey, Ez = induced_E_about_z(grid, dIdt=dIdt, scale=(N/max(L, 1e-9))*max(R, 1e-9))

        # Clear plots + remove old cbar
        self.ax3d.cla()
        if self.ax2d is not None:
            self.ax2d.cla()
        if self._cbar is not None:
            try:
                self._cbar.remove()
            except Exception:
                pass
            self._cbar = None

        # 3D axes
        self.ax3d.set_xlabel("X [m]")
        self.ax3d.set_ylabel("Y [m]")
        self.ax3d.set_zlabel("Z [m]")
        self.ax3d.set_xlim(-bounds, bounds)
        self.ax3d.set_ylim(-bounds, bounds)
        self.ax3d.set_zlim(-bounds, bounds)

        # Draw wire
        self.ax3d.plot(wire[:, 0], wire[:, 1], wire[:, 2], color="darkorange", lw=1.8, alpha=0.95)

        # --- Choose a consistent B scale for colorbar and arrows (A) ---
        # We use a percentile clip to avoid singular spikes dominating.
        bclip_global = np.percentile(Bmag, 95)
        bclip_global = max(bclip_global, 1e-18)
        bnorm = Normalize(vmin=0.0, vmax=bclip_global)
        bmap = plt.cm.Blues

        # Quiver: arrow length = strength (normalize=False) + thin arrows (C)
        if show_quiver:
            step = max(1, quiver_step)
            xs = grid.X[::step, ::step, ::step]
            ys = grid.Y[::step, ::step, ::step]
            zs = grid.Z[::step, ::step, ::step]
            bxs = Bx[::step, ::step, ::step]
            bys = By[::step, ::step, ::step]
            bzs = Bz[::step, ::step, ::step]

            bmag_s = np.sqrt(bxs*bxs + bys*bys + bzs*bzs) + 1e-18

            # arrow scaling relative to bclip_global (Tesla)
            scale = (arrow_scale / bclip_global)

            # per-arrow colors (flatten to (N,4))
            rgba = bmap(bnorm(bmag_s)).reshape(-1, 4)

            Xf = xs.ravel(); Yf = ys.ravel(); Zf = zs.ravel()
            U = (bxs * scale).ravel()
            V = (bys * scale).ravel()
            W = (bzs * scale).ravel()

            try:
                self.ax3d.quiver(
                    Xf, Yf, Zf, U, V, W,
                    length=1.0, normalize=False,
                    color=rgba, alpha=0.60, linewidth=0.25
                )
            except ValueError:
                self.ax3d.quiver(
                    Xf, Yf, Zf, U, V, W,
                    length=1.0, normalize=False,
                    color="royalblue", alpha=0.55, linewidth=0.25
                )

            # E arrows if dIdt != 0 (kept light)
            if abs(dIdt) > 1e-12:
                exs = Ex[::step, ::step, ::step]
                eys = Ey[::step, ::step, ::step]
                ezs = Ez[::step, ::step, ::step]
                emag_s = np.sqrt(exs*exs + eys*eys + ezs*ezs) + 1e-18
                eclip = np.percentile(emag_s, 95) if np.any(emag_s > 0) else 1.0
                eclip = max(eclip, 1e-18)

                escale = (0.7*arrow_scale / eclip)
                en = np.clip(emag_s / eclip, 0, 1)
                ergba = plt.cm.Reds(en).reshape(-1, 4)

                Ue = (exs * escale).ravel()
                Ve = (eys * escale).ravel()
                We = (ezs * escale).ravel()

                try:
                    self.ax3d.quiver(
                        Xf, Yf, Zf, Ue, Ve, We,
                        length=1.0, normalize=False,
                        color=ergba, alpha=0.35, linewidth=0.22
                    )
                except ValueError:
                    self.ax3d.quiver(
                        Xf, Yf, Zf, Ue, Ve, We,
                        length=1.0, normalize=False,
                        color="crimson", alpha=0.30, linewidth=0.22
                    )

        # B fieldlines (streamlines) with coil-type seeds (C)
        if show_B_lines and n_lines > 0:
            seeds = build_seeds(kind, R=R, L=L)
            if len(seeds) > n_lines:
                # pick evenly spaced seeds
                idx = np.linspace(0, len(seeds) - 1, n_lines).astype(int)
                seeds = [seeds[i] for i in idx]

            for s in seeds:
                fwd = integrate_fieldline(grid, Bx, By, Bz, s, ds=0.22, n_steps=line_steps, direction=+1)
                bwd = integrate_fieldline(grid, Bx, By, Bz, s, ds=0.22, n_steps=line_steps, direction=-1)
                if len(fwd) > 5:
                    self.ax3d.plot(fwd[:, 0], fwd[:, 1], fwd[:, 2], color="royalblue", alpha=0.55, lw=1.0)
                if len(bwd) > 5:
                    self.ax3d.plot(bwd[:, 0], bwd[:, 1], bwd[:, 2], color="royalblue", alpha=0.55, lw=1.0)

        # E “fieldlines”: circles
        if show_E_lines and abs(dIdt) > 1e-12:
            draw_E_circles(self.ax3d, R=R, zlim=bounds)

        self.ax3d.view_init(elev=20, azim=40)

        # Heatmap |B| at z≈0 (A)
        if self.ax2d is not None:
            k0 = int(np.argmin(np.abs(grid.z - 0.0)))
            Bmid = Bmag[:, :, k0]  # Tesla
            im = self.ax2d.imshow(
                np.log10(Bmid.T + 1e-20),
                origin="lower",
                extent=[-bounds, bounds, -bounds, bounds],
                aspect="equal",
                cmap="viridis"
            )
            self.ax2d.set_title("Mid-plane z≈0: log10(|B| [T])")
            self.ax2d.set_xlabel("X [m]")
            self.ax2d.set_ylabel("Y [m]")
            self._cbar = self.fig.colorbar(im, ax=self.ax2d, fraction=0.046, pad=0.04)
            self._cbar.set_label("log10(T)")

        # Add B colorbar for quiver/lines (A)
        # Works even if quiver falls back to a single color; scale is still informative.
        sm = ScalarMappable(norm=bnorm, cmap=bmap)
        sm.set_array([])
        # place on 3D axes
        cbarB = self.fig.colorbar(sm, ax=self.ax3d, fraction=0.035, pad=0.02)
        cbarB.set_label("|B| [T] (clipped at p95)")

        self.fig.suptitle(
            f"{kind} | N={N} | R={R:.3g} m | L={L:.3g} m | I={I:.3g} A | "
            f"dI/dt={dIdt:.3g} A/s | res={res} | poly={poly_pts} | cache={'MISS' if recompute else 'HIT'}",
            fontsize=10
        )
        self.fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.95])
        self.canvas.draw()
        self.lbl_status.config(text="Done.")

    # ----------------------------
    # Sidebar build helpers
    # ----------------------------
    def _add_labeled_entry(self, parent, label, var, key=None):
        block = ttk.Frame(parent); block.pack(fill=tk.X, pady=3)
        ttk.Label(block, text=label).pack(anchor="w")
        e = ttk.Entry(block, textvariable=var)
        e.pack(fill=tk.X)
        if key is not None:
            self._entry_refs[key] = e
        return e

    def _add_labeled_spin(self, parent, label, var, from_, to_, increment=1, key=None):
        block = ttk.Frame(parent); block.pack(fill=tk.X, pady=3)
        ttk.Label(block, text=label).pack(anchor="w")
        sp = ttk.Spinbox(block, from_=from_, to=to_, increment=increment, textvariable=var)
        sp.pack(fill=tk.X)
        if key is not None:
            self._spin_refs[key] = sp
        return sp


def main():
    app = HybridCoilGUI()
    app.mainloop()


if __name__ == "__main__":
    main()