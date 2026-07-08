import numpy as np
import tkinter as tk
from dataclasses import dataclass

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

MU0 = 4e-7 * np.pi


@dataclass
class Grid3D:
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    X: np.ndarray
    Y: np.ndarray
    Z: np.ndarray


def make_grid(xlim=3.0, ylim=3.0, zlim=6.0, nx=9, ny=9, nz=17) -> Grid3D:
    x = np.linspace(-xlim, xlim, nx)
    y = np.linspace(-ylim, ylim, ny)
    z = np.linspace(-zlim, zlim, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
    return Grid3D(x, y, z, X, Y, Z)


def make_coil(n_windings: int, radius: float, length: float, pts_per_turn: int = 120):
    theta = np.linspace(0, 2 * np.pi * n_windings, n_windings * pts_per_turn)
    z = np.linspace(-length / 2, length / 2, n_windings * pts_per_turn)
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    return x, y, z


def biot_savart_B_on_grid(
        grid: Grid3D,
        n_windings: int,
        radius: float,
        length: float,
        current_I: float,
        segments_per_loop: int = 90,
):
    """
    B-veld van een finite solenoid benaderd als som van N circulaire lussen.
    Elke lus wordt gediscretiseerd in 'segments_per_loop' segmenten (Biot–Savart).
    """
    # Loop-posities langs z
    if n_windings <= 0:
        return np.zeros_like(grid.X), np.zeros_like(grid.Y), np.zeros_like(grid.Z)

    # Plaats windingen gelijkmatig over de lengte
    z_loops = np.linspace(-length / 2, length / 2, n_windings)

    # Discretiseer een cirkel
    phi = np.linspace(0, 2 * np.pi, segments_per_loop, endpoint=False)
    dphi = 2 * np.pi / segments_per_loop

    # Segment middens op de cirkel
    x_seg = radius * np.cos(phi)
    y_seg = radius * np.sin(phi)
    z_seg0 = np.zeros_like(phi)

    # dl vector (tangent) * dphi
    # r'(phi) = (-R sin, R cos, 0)
    dlx = -radius * np.sin(phi) * dphi
    dly =  radius * np.cos(phi) * dphi
    dlz = np.zeros_like(phi)

    # Veld arrays
    Bx = np.zeros_like(grid.X, dtype=float)
    By = np.zeros_like(grid.Y, dtype=float)
    Bz = np.zeros_like(grid.Z, dtype=float)

    # Constant factor
    c = MU0 * current_I / (4 * np.pi)

    # Flatten grid points for vectorized math
    Px = grid.X.reshape(-1)
    Py = grid.Y.reshape(-1)
    Pz = grid.Z.reshape(-1)

    Bx_f = np.zeros_like(Px)
    By_f = np.zeros_like(Py)
    Bz_f = np.zeros_like(Pz)

    # Iterate loops (N up to ~20-30 is ok)
    for z0 in z_loops:
        # Segment coordinates for this loop
        sx = x_seg
        sy = y_seg
        sz = z_seg0 + z0

        # Broadcast: points (P) vs segments (S)
        # r_vec = P - S
        rx = Px[:, None] - sx[None, :]
        ry = Py[:, None] - sy[None, :]
        rz = Pz[:, None] - sz[None, :]

        r2 = rx * rx + ry * ry + rz * rz + 1e-18
        r3 = r2 * np.sqrt(r2)

        # dl x r
        cxr_x = dly[None, :] * rz - dlz[None, :] * ry
        cxr_y = dlz[None, :] * rx - dlx[None, :] * rz
        cxr_z = dlx[None, :] * ry - dly[None, :] * rx

        dBx = c * (cxr_x / r3)
        dBy = c * (cxr_y / r3)
        dBz = c * (cxr_z / r3)

        # Sum over segments
        Bx_f += np.sum(dBx, axis=1)
        By_f += np.sum(dBy, axis=1)
        Bz_f += np.sum(dBz, axis=1)

    # Reshape back
    Bx = Bx_f.reshape(grid.X.shape)
    By = By_f.reshape(grid.Y.shape)
    Bz = Bz_f.reshape(grid.Z.shape)
    return Bx, By, Bz


def induced_E_on_grid_faraday(
        grid: Grid3D,
        n_windings: int,
        radius: float,
        length: float,
        dIdt: float,
):
    """
    E-veld door Faraday voor 'lange' solenoid-approx:
      B_inside ≈ μ0 * n * I  (n = N/length)
      dB/dt = μ0 * n * dI/dt

    Induced E is azimutal (phi-richting):
      for r <= R:   E_phi = - (r/2) * dB/dt
      for r >  R:   E_phi = - (R^2/(2r)) * dB/dt
    """
    if length <= 1e-9:
        n = 0.0
    else:
        n = n_windings / length

    dBdt = MU0 * n * dIdt

    X, Y, Z = grid.X, grid.Y, grid.Z
    r = np.sqrt(X * X + Y * Y) + 1e-12

    inside = r <= radius
    Ephi = np.empty_like(r)
    Ephi[inside] = -(r[inside] / 2.0) * dBdt
    Ephi[~inside] = -(radius * radius / (2.0 * r[~inside])) * dBdt

    # Convert (Ephi) -> (Ex,Ey)
    # e_phi = (-sinφ, cosφ, 0) = (-y/r, x/r, 0)
    Ex = Ephi * (-Y / r)
    Ey = Ephi * ( X / r)
    Ez = np.zeros_like(Ex)
    return Ex, Ey, Ez


def trilinear_interp_vector(grid: Grid3D, Vx, Vy, Vz, p):
    """
    Trilinear interpolation of vector field on a regular grid.
    p: (x,y,z) scalar floats.
    """
    x, y, z = p
    # bounds check
    if x < grid.x[0] or x > grid.x[-1] or y < grid.y[0] or y > grid.y[-1] or z < grid.z[0] or z > grid.z[-1]:
        return None

    # find indices
    ix = np.searchsorted(grid.x, x) - 1
    iy = np.searchsorted(grid.y, y) - 1
    iz = np.searchsorted(grid.z, z) - 1
    ix = int(np.clip(ix, 0, len(grid.x) - 2))
    iy = int(np.clip(iy, 0, len(grid.y) - 2))
    iz = int(np.clip(iz, 0, len(grid.z) - 2))

    x0, x1 = grid.x[ix], grid.x[ix + 1]
    y0, y1 = grid.y[iy], grid.y[iy + 1]
    z0, z1 = grid.z[iz], grid.z[iz + 1]

    tx = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
    ty = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
    tz = 0.0 if z1 == z0 else (z - z0) / (z1 - z0)

    def lerp(a, b, t): return a * (1 - t) + b * t

    # corners
    # order: (ix/ix+1, iy/iy+1, iz/iz+1)
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


def integrate_fieldline(grid: Grid3D, Vx, Vy, Vz, seed, ds=0.20, n_steps=160, direction=+1):
    """
    Integrate a field line using RK4 on interpolated vector field.
    direction: +1 forward, -1 backward
    """
    pts = [np.array(seed, dtype=float)]
    p = np.array(seed, dtype=float)

    for _ in range(n_steps):
        v1 = trilinear_interp_vector(grid, Vx, Vy, Vz, p)
        if v1 is None:
            break
        n1 = np.linalg.norm(v1)
        if n1 < 1e-15:
            break
        k1 = direction * ds * (v1 / n1)

        v2 = trilinear_interp_vector(grid, Vx, Vy, Vz, p + 0.5 * k1)
        if v2 is None:
            break
        n2 = np.linalg.norm(v2)
        if n2 < 1e-15:
            break
        k2 = direction * ds * (v2 / n2)

        v3 = trilinear_interp_vector(grid, Vx, Vy, Vz, p + 0.5 * k2)
        if v3 is None:
            break
        n3 = np.linalg.norm(v3)
        if n3 < 1e-15:
            break
        k3 = direction * ds * (v3 / n3)

        v4 = trilinear_interp_vector(grid, Vx, Vy, Vz, p + k3)
        if v4 is None:
            break
        n4 = np.linalg.norm(v4)
        if n4 < 1e-15:
            break
        k4 = direction * ds * (v4 / n4)

        p = p + (k1 + 2 * k2 + 2 * k3 + k4) / 6.0
        pts.append(p.copy())

    return np.array(pts)


def build_B_seeds(radius: float):
    # Seeds rond/naast de spoel om mooie lijnen te krijgen
    seeds = []
    for rr in [0.5 * radius, 0.9 * radius, 1.2 * radius, 1.8 * radius, 2.4 * radius]:
        for ang in np.linspace(0, 2 * np.pi, 8, endpoint=False):
            seeds.append((rr * np.cos(ang), rr * np.sin(ang), 0.0))
    # Extra seeds boven/onder
    for zz in [-2.5, 2.5]:
        for rr in [0.8 * radius, 1.6 * radius]:
            for ang in np.linspace(0, 2 * np.pi, 6, endpoint=False):
                seeds.append((rr * np.cos(ang), rr * np.sin(ang), zz))
    return seeds


def draw_E_fieldlines(ax, radius: float, zlim: float = 6.0):
    # In dit model zijn E-veldlijnen cirkels rond de z-as.
    # We tekenen cirkels op enkele z-planes.
    zs = np.linspace(-zlim * 0.6, zlim * 0.6, 5)
    rs = [0.5 * radius, 1.0 * radius, 1.5 * radius, 2.2 * radius]
    t = np.linspace(0, 2 * np.pi, 200)
    for z in zs:
        for r in rs:
            x = r * np.cos(t)
            y = r * np.sin(t)
            ax.plot(x, y, z * np.ones_like(t), color="crimson", alpha=0.35, linewidth=1.0)


class App:
    def __init__(self, root):
        self.root = root
        root.title("3D Spoel: B- en E-veld (veldlines buiten + sterkte)")

        # Controls
        left = tk.Frame(root)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Vars
        self.v_wind = tk.IntVar(value=10)
        self.v_radius = tk.DoubleVar(value=1.0)
        self.v_length = tk.DoubleVar(value=8.0)
        self.v_I = tk.DoubleVar(value=1.0)
        self.v_dIdt = tk.DoubleVar(value=0.0)

        self.v_show_quiver = tk.IntVar(value=1)
        self.v_show_B_lines = tk.IntVar(value=1)
        self.v_show_E_lines = tk.IntVar(value=1)

        # Sliders
        self._add_slider(left, "Windingen (N)", self.v_wind, 1, 25, 1, self.update)
        self._add_slider(left, "Straal (R)", self.v_radius, 0.4, 2.5, 0.1, self.update)
        self._add_slider(left, "Lengte (L)", self.v_length, 2.0, 14.0, 0.5, self.update)
        self._add_slider(left, "Stroom I (A)", self.v_I, -5.0, 5.0, 0.5, self.update)

        tk.Label(left, text="dI/dt (A/s) → E-veld", pady=6).pack()
        tk.Scale(left, from_=-20.0, to=20.0, resolution=1.0, orient=tk.HORIZONTAL,
                 variable=self.v_dIdt, command=lambda _=None: self.update()).pack(fill=tk.X)

        tk.Checkbutton(left, text="Toon pijlen (sterkte = lengte)", variable=self.v_show_quiver,
                       command=self.update).pack(anchor="w", pady=(10, 0))
        tk.Checkbutton(left, text="Toon B-veldlijnen (buiten+binnen)", variable=self.v_show_B_lines,
                       command=self.update).pack(anchor="w")
        tk.Checkbutton(left, text="Toon E-veldlijnen (cirkels)", variable=self.v_show_E_lines,
                       command=self.update).pack(anchor="w")

        tk.Button(left, text="Reset view", command=self.update).pack(fill=tk.X, pady=(12, 0))

        # Figure
        self.fig = plt.Figure(figsize=(10.5, 6.5), dpi=100)
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.update()

    def _add_slider(self, parent, label, var, a, b, step, cmd):
        tk.Label(parent, text=label, pady=6).pack()
        tk.Scale(parent, from_=a, to=b, resolution=step, orient=tk.HORIZONTAL,
                 variable=var, command=lambda _=None: cmd()).pack(fill=tk.X)

    def update(self):
        N = int(self.v_wind.get())
        R = float(self.v_radius.get())
        L = float(self.v_length.get())
        I = float(self.v_I.get())
        dIdt = float(self.v_dIdt.get())

        # Grid size scales a bit with coil to keep outside visible
        xlim = max(3.0, 1.35 * (R + 1.5))
        ylim = xlim
        zlim = max(6.0, 0.9 * (L / 2 + 3.0))

        grid = make_grid(xlim=xlim, ylim=ylim, zlim=zlim, nx=9, ny=9, nz=17)

        # Compute fields
        Bx, By, Bz = biot_savart_B_on_grid(grid, N, R, L, I, segments_per_loop=90)
        Ex, Ey, Ez = induced_E_on_grid_faraday(grid, N, R, L, dIdt)

        # Clear and redraw
        self.ax.cla()
        self.ax.set_title("Spoel + B (blauw) + E (rood)\nPijl-lengte = sterkte, lijnen = veldlijnen", fontsize=12)

        # Coil
        cx, cy, cz = make_coil(N, R, L)
        self.ax.plot3D(cx, cy, cz, color="darkorange", linewidth=2.0, label="Spoel")

        # Quiver (subsample to reduce clutter)
        if self.v_show_quiver.get() == 1:
            # Flatten
            Xf = grid.X.ravel()
            Yf = grid.Y.ravel()
            Zf = grid.Z.ravel()

            Bxf = Bx.ravel()
            Byf = By.ravel()
            Bzf = Bz.ravel()

            Exf = Ex.ravel()
            Eyf = Ey.ravel()
            Ezf = Ez.ravel()

            # Scale arrows by magnitude (NO normalize)
            Bmag = np.sqrt(Bxf**2 + Byf**2 + Bzf**2) + 1e-18
            Emag = np.sqrt(Exf**2 + Eyf**2 + Ezf**2) + 1e-18

            # Avoid insane spikes near wire: clip high percentiles for nicer visuals
            Bclip = np.percentile(Bmag, 95)
            Eclip = np.percentile(Emag, 95) if np.any(Emag > 0) else 1.0

            Bscale = 0.9 / max(Bclip, 1e-18)
            Escale = 0.9 / max(Eclip, 1e-18)

            # Colors by magnitude (simple normalization)
            Bc = plt.cm.Blues(np.clip(Bmag / max(Bclip, 1e-18), 0, 1))
            Ec = plt.cm.Reds(np.clip(Emag / max(Eclip, 1e-18), 0, 1))

            # Plot B arrows
            self.ax.quiver(
                Xf, Yf, Zf,
                Bxf * Bscale, Byf * Bscale, Bzf * Bscale,
                length=1.0, normalize=False, colors=Bc, alpha=0.70, linewidth=0.4
            )

            # Plot E arrows (only if dIdt != 0)
            if abs(dIdt) > 1e-12:
                self.ax.quiver(
                    Xf, Yf, Zf,
                    Exf * Escale, Eyf * Escale, Ezf * Escale,
                    length=1.0, normalize=False, colors=Ec, alpha=0.55, linewidth=0.4
                )

        # B fieldlines (integrated)
        if self.v_show_B_lines.get() == 1:
            seeds = build_B_seeds(R)
            for s in seeds[:28]:  # limit count for speed
                fwd = integrate_fieldline(grid, Bx, By, Bz, s, ds=0.22, n_steps=140, direction=+1)
                bwd = integrate_fieldline(grid, Bx, By, Bz, s, ds=0.22, n_steps=140, direction=-1)
                if len(fwd) > 5:
                    self.ax.plot(fwd[:, 0], fwd[:, 1], fwd[:, 2], color="royalblue", alpha=0.55, linewidth=1.0)
                if len(bwd) > 5:
                    self.ax.plot(bwd[:, 0], bwd[:, 1], bwd[:, 2], color="royalblue", alpha=0.55, linewidth=1.0)

        # E fieldlines (circles)
        if self.v_show_E_lines.get() == 1 and abs(dIdt) > 1e-12:
            draw_E_fieldlines(self.ax, R, zlim=zlim)

        # Axes & view
        self.ax.set_xlim(-xlim, xlim)
        self.ax.set_ylim(-ylim, ylim)
        self.ax.set_zlim(-zlim, zlim)
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.set_zlabel("Z")

        # Legend-like text
        info = f"N={N}, R={R:.2f}, L={L:.2f}, I={I:.2f} A, dI/dt={dIdt:.1f} A/s"
        self.ax.text2D(0.02, 0.02, info, transform=self.ax.transAxes, fontsize=9)

        self.canvas.draw()


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()