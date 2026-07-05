import numpy as np
import matplotlib
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons
import sys

# --- 0. BACKEND SETUP ---
# Set backend to TkAgg for interactive window support
try:
    matplotlib.use('TkAgg')
except:
    print("Warning: TkAgg backend not available. Plots may not be interactive.")

# --- 1. SST CONSTANTS ---
class SSTCanon:
    V_SWIRL = 1.09384563e6   # m/s
    MU0 = 4 * np.pi * 1e-7   # Vacuum Permeability
    # Geometry Defaults for Saw Coil
    STEP_FWD = 11
    STEP_BWD = -9
    POWER = 2.2

# --- 2. PHYSICS ENGINE ---
class SSTPhysics:
    """
    Unified Physics Engine.
    Calculates B-Field, Vector Potential (A), and Gravity Gradient.
    """

    @staticmethod
    def biot_savart_vectorized(grid_flat, wire_points, current=1.0, mode='B'):
        """Computes B or A field using vectorized Numpy."""
        factor_B = (SSTCanon.MU0 * current) / (4.0 * np.pi)
        factor_A = (SSTCanon.MU0 * current) / (4.0 * np.pi)

        dl = np.diff(wire_points, axis=0)
        mid = 0.5 * (wire_points[:-1] + wire_points[1:])

        R_vec = grid_flat[:, None, :] - mid[None, :, :]
        r_mag = np.linalg.norm(R_vec, axis=-1)
        r_mag[r_mag < 1e-6] = 1e-6

        if mode == 'B':
            cross = np.cross(dl[None, :, :], R_vec)
            integrand = cross / (r_mag[..., None]**3)
            return factor_B * np.sum(integrand, axis=1)

        elif mode == 'A':
            integrand = dl[None, :, :] / (r_mag[..., None])
            return factor_A * np.sum(integrand, axis=1)

    @staticmethod
    def dipole_grid_vectorized(grid_flat, positions, moments, mode='B'):
        """Calculates field from Point Dipoles (Halbach Magnets)."""
        factor = SSTCanon.MU0 / (4.0 * np.pi)
        R_vec = grid_flat[:, None, :] - positions[None, :, :]
        r_mag = np.linalg.norm(R_vec, axis=-1)
        r_mag[r_mag < 1e-6] = 1e-6

        if mode == 'B':
            m_dot_r = np.einsum('ijk, jk -> ij', R_vec, moments)
            term1 = 3.0 * m_dot_r[..., None] * R_vec
            term2 = moments[None, :, :] * (r_mag[..., None]**2)
            integrand = (term1 - term2) / (r_mag[..., None]**5)
            return factor * np.sum(integrand, axis=1)
        elif mode == 'A':
            cross = np.cross(moments[None, :, :], R_vec)
            integrand = cross / (r_mag[..., None]**3)
            return factor * np.sum(integrand, axis=1)
        return np.zeros_like(grid_flat)

    @staticmethod
    def compute_gravity_force(B_flat, grid_shape, bounds):
        """Gravity Force Vector (F_g) = Gradient( |B|^2 )"""
        Bx = B_flat[:, 0].reshape(grid_shape)
        By = B_flat[:, 1].reshape(grid_shape)
        Bz = B_flat[:, 2].reshape(grid_shape)

        E_density = Bx**2 + By**2 + Bz**2
        gz, gy, gx = np.gradient(E_density) # Note: Gradient order

        return np.stack([gx.flatten(), gy.flatten(), gz.flatten()], axis=-1)

# --- 3. GEOMETRY GENERATORS ---

def alternating_skip_indices(S, step_fwd, step_bwd, n_pairs, start=1):
    idx = start
    seq = [idx]
    for k in range(2 * n_pairs):
        if k % 2 == 0: idx = (idx + step_fwd - 1) % S + 1
        else:          idx = (idx + step_bwd - 1) % S + 1
        seq.append(idx)
    return np.array(seq, dtype=int)

def r_profile(s, Rb, Rt, profile, power):
    if profile == 'Exponential': return Rb + (Rt - Rb) * (s**power)
    elif profile == 'Inverse Exp': return Rt - (Rt - Rb) * (s**power)
    else: return Rb + (Rt - Rb) * s

def generate_saw_bowl(Rb, Rt, Hc, layers, profile='Exponential', mode='Curved'):
    S = 40
    step_fwd = SSTCanon.STEP_FWD; step_bwd = SSTCanon.STEP_BWD
    seq = alternating_skip_indices(S, step_fwd, step_bwd, int(layers))
    slot_angles = np.linspace(0, 2*np.pi, S, endpoint=False) - np.pi/2.0
    phases = []
    offsets = [0.0, 2*np.pi/3, 4*np.pi/3]

    for offset in offsets:
        N_segs = len(seq) - 1
        s_nodes = np.linspace(0, 1, N_segs + 1)
        r_nodes = r_profile(s_nodes, Rb, Rt, profile, SSTCanon.POWER)

        if mode == 'Curved':
            samples_per_seg = 8
            z_nodes = s_nodes * Hc
            xs, ys, zs = [], [], []
            for k in range(N_segs):
                i0, i1 = seq[k]-1, seq[k+1]-1
                a0 = slot_angles[i0] + offset; a1 = slot_angles[i1] + offset
                da = (a1 - a0 + np.pi) % (2*np.pi) - np.pi
                t = np.linspace(0, 1, samples_per_seg, endpoint=False)
                a_line = a0 + t * da
                r_line = np.linspace(r_nodes[k], r_nodes[k+1], samples_per_seg, endpoint=False)
                z_line = np.linspace(z_nodes[k], z_nodes[k+1], samples_per_seg, endpoint=False)
                xs.append(r_line * np.cos(a_line)); ys.append(r_line * np.sin(a_line)); zs.append(z_line)
            phases.append(np.stack([np.concatenate(xs), np.concatenate(ys), np.concatenate(zs)], axis=-1))
        else:
            z_nodes = s_nodes * Hc
            angles = slot_angles[seq-1] + offset
            X = r_nodes * np.cos(angles); Y = r_nodes * np.sin(angles); Z = z_nodes
            phases.append(np.stack([X, Y, Z], axis=-1))
    return phases

def generate_simple_solenoid(R, H, turns):
    points = 300
    t = np.linspace(0, turns * 2 * np.pi, points)
    z = np.linspace(0, H, points)
    x = R * np.cos(t); y = R * np.sin(t)
    return [np.stack([x, y, z], axis=-1)]

def generate_halbach_rings(R, z_sep, n_mag=16):
    rings = []
    for z_pos in [z_sep, 0]: # Stacked vertically
        positions = []; moments = []
        for i in range(n_mag):
            theta = 2 * np.pi * i / n_mag
            px = R * np.cos(theta); py = R * np.sin(theta); pz = z_pos
            alpha = 2 * theta # Halbach k=1
            mx = np.cos(alpha); my = np.sin(alpha); mz = 0.0
            positions.append([px, py, pz]); moments.append([mx, my, mz])
        rings.append((np.array(positions), np.array(moments)))
    return rings

# --- 4. THE APPLICATION ---
class SSTFullApp:
    def __init__(self):
        self.fig = plt.figure(figsize=(15, 9))
        self.ax = self.fig.add_subplot(111, projection='3d')
        plt.subplots_adjust(left=0.05, right=0.65, bottom=0.1)

        # Initial Grid Params
        self.grid_res = 8
        self.bounds = 2.0
        self.setup_grid()

        self.params = { 'Rb': 0.5, 'Rt': 1.5, 'Layers': 20, 'Hc': 1.5 }

        self.init_gui()
        self.update()

    def setup_grid(self):
        # Called whenever Resolution or Volume changes
        vals = np.linspace(-self.bounds, self.bounds, self.grid_res)
        self.X, self.Y, self.Z = np.meshgrid(vals, vals, vals, indexing='ij')
        self.grid_flat = np.stack([self.X.flatten(), self.Y.flatten(), self.Z.flatten()], axis=-1)
        self.grid_shape = self.X.shape

    def init_gui(self):
        # --- LEFT: GEOMETRY SLIDERS ---
        ax_Rb = plt.axes([0.10, 0.08, 0.45, 0.03])
        ax_Rt = plt.axes([0.10, 0.04, 0.45, 0.03])
        ax_L  = plt.axes([0.10, 0.005, 0.20, 0.03])
        ax_H  = plt.axes([0.35, 0.005, 0.20, 0.03])

        self.sl_Rb = Slider(ax_Rb, 'Radius Base', 0.1, 3.0, valinit=self.params['Rb'])
        self.sl_Rt = Slider(ax_Rt, 'Radius Top', 0.1, 3.0, valinit=self.params['Rt'])
        self.sl_L  = Slider(ax_L,  'Layers', 5, 50, valinit=self.params['Layers'], valstep=1)
        self.sl_H  = Slider(ax_H,  'Height', 0.1, 3.0, valinit=self.params['Hc'])

        for s in [self.sl_Rb, self.sl_Rt, self.sl_L, self.sl_H]:
            s.on_changed(self.update_wrapper)

        # --- RIGHT: CONTROLS ---

        # 1. Physics Grid Controls (NEW)
        ax_res = plt.axes([0.70, 0.92, 0.25, 0.03])
        ax_vol = plt.axes([0.70, 0.88, 0.25, 0.03])
        ax_vis = plt.axes([0.70, 0.84, 0.25, 0.03])

        self.sl_Res = Slider(ax_res, 'Grid Density', 4, 15, valinit=8, valstep=1)
        self.sl_Vol = Slider(ax_vol, 'View Vol', 1.0, 5.0, valinit=2.0)
        self.sl_Vis = Slider(ax_vis, 'Filter %', 0, 95, valinit=30) # Vis threshold

        self.sl_Res.on_changed(self.on_grid_change)
        self.sl_Vol.on_changed(self.on_grid_change)
        self.sl_Vis.on_changed(self.update_wrapper)

        # 2. Source Geometry
        ax_geom = plt.axes([0.70, 0.65, 0.25, 0.15])
        self.rad_geom = RadioButtons(ax_geom, ('Saw Coil (Sliders)', 'Simple Solenoid', 'Halbach Rings'), active=0)
        self.rad_geom.on_clicked(self.update_wrapper)
        ax_geom.set_title("Source Coil")

        # 3. Hull Profile
        ax_prof = plt.axes([0.70, 0.50, 0.25, 0.12])
        self.rad_prof = RadioButtons(ax_prof, ('Exponential', 'Linear', 'Inverse Exp'), active=0)
        self.rad_prof.on_clicked(self.update_wrapper)
        ax_prof.set_title("Saw: Hull Profile")

        # 4. Wire Mode
        ax_wire = plt.axes([0.70, 0.40, 0.25, 0.08])
        self.rad_wire = RadioButtons(ax_wire, ('Curved', 'Straight'), active=0)
        self.rad_wire.on_clicked(self.update_wrapper)
        ax_wire.set_title("Saw: Wire Mode")

        # 5. Physics View
        ax_phys = plt.axes([0.70, 0.15, 0.25, 0.20])
        self.rad_phys = RadioButtons(ax_phys, ('Magnetic Field (B)', 'Vector Potential (A)', 'Gravity Vector (Fg)', 'Helicity Density'), active=0)
        self.rad_phys.on_clicked(self.update_wrapper)
        ax_phys.set_title("SST Physics View")

    def on_grid_change(self, val):
        # Rebuild grid when Res or Volume changes
        self.grid_res = int(self.sl_Res.val)
        self.bounds = self.sl_Vol.val
        self.setup_grid()
        self.update()

    def update_wrapper(self, val=None):
        self.update()

    def update(self):
        self.ax.clear()

        mode = self.rad_geom.value_selected
        profile = self.rad_prof.value_selected
        wire_mode = self.rad_wire.value_selected
        phys_mode = self.rad_phys.value_selected

        wires = []; dipoles = []; col_wire = 'orange'

        # 1. GENERATE GEOMETRY
        if mode == 'Saw Coil (Sliders)':
            wires = generate_saw_bowl(self.sl_Rb.val, self.sl_Rt.val, self.sl_H.val, self.sl_L.val, profile, wire_mode)
        elif mode == 'Simple Solenoid':
            wires = generate_simple_solenoid(R=self.sl_Rb.val, H=self.sl_H.val, turns=int(self.sl_L.val))
            col_wire = 'lime'
        elif mode == 'Halbach Rings':
            dipoles = generate_halbach_rings(R=self.sl_Rb.val, z_sep=self.sl_H.val)
            col_wire = 'cyan'

        # 2. COMPUTE PHYSICS
        B_flat = np.zeros_like(self.grid_flat)
        A_flat = np.zeros_like(self.grid_flat)

        # B-Field
        for w in wires: B_flat += SSTPhysics.biot_savart_vectorized(self.grid_flat, w, mode='B')
        for (pos, mom) in dipoles: B_flat += SSTPhysics.dipole_grid_vectorized(self.grid_flat, pos, mom, mode='B')

        # A-Field (Lazy load)
        calc_A = (phys_mode == 'Vector Potential (A)' or phys_mode == 'Helicity Density')
        if calc_A:
            for w in wires: A_flat += SSTPhysics.biot_savart_vectorized(self.grid_flat, w, mode='A')
            for (pos, mom) in dipoles: A_flat += SSTPhysics.dipole_grid_vectorized(self.grid_flat, pos, mom, mode='A')

        # Select Vectors/Scalars
        vectors = B_flat; scalars = np.linalg.norm(B_flat, axis=-1)

        if phys_mode == 'Vector Potential (A)':
            vectors = A_flat; scalars = np.linalg.norm(A_flat, axis=-1)
        elif phys_mode == 'Gravity Vector (Fg)':
            Fg = SSTPhysics.compute_gravity_force(B_flat, self.grid_shape, self.bounds)
            vectors = Fg; scalars = np.linalg.norm(Fg, axis=-1)
        elif phys_mode == 'Helicity Density':
            vectors = B_flat; scalars = np.sum(A_flat * B_flat, axis=-1)

        # 3. VISUALIZATION
        # Apply Threshold
        threshold_val = np.percentile(np.abs(scalars), self.sl_Vis.val)
        mask = np.abs(scalars) > threshold_val

        if np.any(mask):
            X, Y, Z = self.grid_flat[mask, 0], self.grid_flat[mask, 1], self.grid_flat[mask, 2]
            U, V, W = vectors[mask, 0], vectors[mask, 1], vectors[mask, 2]
            C = scalars[mask]

            # Dynamic Alpha Calculation
            # Normalize C for alpha (0.2 to 1.0)
            c_abs = np.abs(C)
            if c_abs.max() > 0:
                alpha_vals = 0.2 + 0.8 * (c_abs / c_abs.max())
            else:
                alpha_vals = 0.5

            # Quiver doesn't support array-based alpha natively in all mpl versions,
            # so we use a loop or just global alpha.
            # For speed/compatibility, we use global alpha but Colormap implies intensity.
            # 'plasma' is excellent for showing intensity variation.
            norm_uvw = np.sqrt(U**2 + V**2 + W**2) + 1e-9
            self.ax.quiver(X, Y, Z, U/norm_uvw, V/norm_uvw, W/norm_uvw,
                           length=0.2 * self.bounds, normalize=True, cmap='plasma', array=C, alpha=0.6)

        # Draw Wires
        for w in wires: self.ax.plot(w[:,0], w[:,1], w[:,2], c=col_wire, lw=1.5, alpha=0.8)
        for (pos, mom) in dipoles: self.ax.quiver(pos[:,0], pos[:,1], pos[:,2], mom[:,0], mom[:,1], mom[:,2], length=0.2, color='red')

        self.ax.set_xlim(-self.bounds, self.bounds); self.ax.set_ylim(-self.bounds, self.bounds); self.ax.set_zlim(-self.bounds, self.bounds)
        self.ax.set_title(f"SST | {mode} | {phys_mode}")
        plt.draw()

if __name__ == "__main__":
    app = SSTFullApp()
    plt.show()