# -----------------------------------------------------------------------------
# SST Field Visualizer: Rodin Starship Coils, Dipole Rings, & Gravity Metrics
# -----------------------------------------------------------------------------
# Integrates:
# 1. Geometry: Rodin Starship Coils, Halbach Dipole Rings, Trefoil Knots
# 2. Physics: B-Field, Vector Potential (A), Helicity (h), SST Gravity Dilation
# 3. Acceleration: Optional C++ 'sstbindings' support with NumPy fallbacks
# 4. Environment: Auto-detects Google Colab (ipympl) vs Local (TkAgg)
# -----------------------------------------------------------------------------

import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, TextBox, CheckButtons
import time

# --- 1. Environment & Backend Setup ---
IN_COLAB = 'google.colab' in sys.modules

if IN_COLAB:
    print("[SST] Environment: Google Colab detected.")
    print("[SST] Info: Ensure you have run '!pip install ipympl' and enabled widgets.")
    # Magic command to enable interactive plot in Colab (must be handled by user in cell usually,
    # but we set the backend here just in case).
    try:
        import ipympl
        plt.switch_backend('ipympl')
    except ImportError:
        print("[SST] Warning: 'ipympl' not found. Visuals may not be interactive.")
else:
    print("[SST] Environment: Local.")
    try:
        import tkinter
        plt.switch_backend('TkAgg')
        print("[SST] Backend: TkAgg")
    except ImportError:
        print("[SST] Warning: TkAgg not found, using default backend.")

# --- 2. SST Canonical Constants [2025-11-21] ---
class SSTCanon:
    V_SWIRL = 1.09384563e6      # Characteristic swirl speed [m/s]
    RHO_CORE = 3.893e18         # Core density [kg/m^3]
    MU0 = 4 * np.pi * 1e-7      # Vacuum permeability (Classical mapping)
    RHO_F = 7.0e-7              # Effective fluid density

# --- 3. Optional C++ Bindings Import ---
_HAS_SST_BINDINGS = False
try:
    import swirl_string_core
    from swirl_string_core import (
        biot_savart_velocity_grid,          # B-field
        biot_savart_vector_potential_grid,  # A-field
        dipole_ring_field_grid              # Dipole B-field
    )
    _HAS_SST_BINDINGS = True
    print("[SST] Acceleration: sstbindings LOADED.")
except ImportError:
    print("[SST] Acceleration: sstbindings NOT FOUND. Using NumPy fallbacks.")

# --- 4. SST Physics Kernel (Metrics & Fallbacks) ---
class SSTGravity:
    """
    SST Physics Engine for Gravity Modification Metrics.
    Derivations based on Vacuum Stress and Frequency Coupling.
    """

    @staticmethod
    def compute_curl(Bx, By, Bz, dx, dy, dz):
        """Calculates Curl (Nabla x B) for Beltrami Shear analysis."""
        # Gradient ordering in np.gradient is axis=0,1,2 (z, y, x usually depending on meshgrid)
        # Assuming meshgrid('ij') -> x(0), y(1), z(2)
        dVz_dy = np.gradient(Bz, axis=1) / dy
        dVy_dz = np.gradient(By, axis=2) / dz

        dVx_dz = np.gradient(Bx, axis=2) / dz
        dVz_dx = np.gradient(Bz, axis=0) / dx

        dVy_dx = np.gradient(By, axis=0) / dx
        dVx_dy = np.gradient(Bx, axis=1) / dy

        Wx = dVz_dy - dVy_dz
        Wy = dVx_dz - dVz_dx
        Wz = dVy_dx - dVx_dy

        return np.stack([Wx, Wy, Wz], axis=-1)

    @staticmethod
    def compute_gravity_dilation(B_vec, omega, B_sat=100.0):
        """
        Calculates Metric 2: SST Gravity Dilation (G_local).
        G_local = 1 - (v_induced / v_swirl)^2
        """
        B_mag = np.linalg.norm(B_vec, axis=-1)

        # Logarithmic frequency scaling
        freq_scale = np.log10(omega) if omega > 1.0 else 0.0

        # Coupling ratio
        coupling = (B_mag / B_sat) * freq_scale

        # G = 1 - coupling^2
        G_map = 1.0 - np.square(coupling)
        return np.clip(G_map, 0.0, 1.0)

    @staticmethod
    def compute_helicity_density(A_field, B_field):
        """Calculates Metric 3: Magnetic Helicity Density (h = A . B)."""
        return np.sum(A_field * B_field, axis=-1)

    # --- NumPy Fallbacks for Field Generation ---
    @staticmethod
    def _numpy_wire_field(grid_flat, wire_points, current=1.0, mode='B'):
        """
        Vectorized Biot-Savart for B or A fields.
        mode='B': (mu0 I / 4pi) * sum( dl x r / r^3 )
        mode='A': (mu0 I / 4pi) * sum( dl / r )
        """
        factor = (SSTCanon.MU0 * current) / (4.0 * np.pi)

        dl = np.diff(wire_points, axis=0)                # [Seg, 3]
        mid = 0.5 * (wire_points[:-1] + wire_points[1:]) # [Seg, 3]

        # R = Grid - Source
        # grid: [N_grid, 1, 3], source: [1, N_seg, 3]
        R_vec = grid_flat[:, None, :] - mid[None, :, :]  # [N_grid, N_seg, 3]
        r_mag = np.linalg.norm(R_vec, axis=-1)           # [N_grid, N_seg]
        r_mag[r_mag < 1e-9] = 1e-9                       # Singularity clamp

        if mode == 'B':
            # dl x R
            cross = np.cross(dl[None, :, :], R_vec)      # [N_grid, N_seg, 3]
            integrand = cross / (r_mag[..., None]**3)
        elif mode == 'A':
            # dl / r
            integrand = dl[None, :, :] / (r_mag[..., None])

        return factor * np.sum(integrand, axis=1)

    @staticmethod
    def _numpy_dipole_field(grid_flat, positions, moments, mode='B'):
        """
        Vectorized Dipole calculations.
        """
        factor = SSTCanon.MU0 / (4.0 * np.pi)

        # R = Grid - Dipole
        R_vec = grid_flat[:, None, :] - positions[None, :, :] # [N_grid, N_dip, 3]
        r_mag = np.linalg.norm(R_vec, axis=-1)                # [N_grid, N_dip]
        r_mag[r_mag < 1e-9] = 1e-9

        if mode == 'B':
            # B = (3(m.r)r - m*r^2) / r^5
            m_dot_r = np.einsum('ijk, jk -> ij', R_vec, moments) # [N_grid, N_dip]

            term1 = 3.0 * m_dot_r[..., None] * R_vec
            term2 = moments[None, :, :] * (r_mag[..., None]**2)
            integrand = (term1 - term2) / (r_mag[..., None]**5)

        elif mode == 'A':
            # A = (m x r) / r^3
            cross = np.cross(moments[None, :, :], R_vec)
            integrand = cross / (r_mag[..., None]**3)

        return factor * np.sum(integrand, axis=1)

# --- 5. Geometry Generators ---
def generate_rodin_starship(R=1.0, r=0.4, num_turns=5, num_points=600):
    theta = np.linspace(0, num_turns * 2 * np.pi, num_points)
    # Rodin topology: phi varies with theta
    phi = (2 + 2/5) * theta
    x = (R + r * np.cos(phi)) * np.cos(theta)
    y = (R + r * np.cos(phi)) * np.sin(theta)
    z = r * np.sin(phi)
    return np.stack([x, y, z], axis=-1)

def generate_dipole_ring(radius, num_magnets, z_offset=0.0, invert=False):
    positions, moments = [], []
    for i in range(num_magnets):
        phi = 2 * np.pi * i / num_magnets
        x, y, z = radius * np.cos(phi), radius * np.sin(phi), z_offset
        # Halbach-style rotation (2x phi)
        mx = np.cos(2 * phi)
        my = np.sin(2 * phi)
        mz = np.cos(phi)
        m = np.array([mx, my, (-1 if invert else 1) * mz])
        m /= np.linalg.norm(m)
        positions.append([x, y, z])
        moments.append(m)
    return np.array(positions), np.array(moments)

def generate_trefoil(scale=1.2, points=600):
    t = np.linspace(0, 2*np.pi, points)
    x = scale * (np.sin(t) + 2 * np.sin(2 * t))
    y = scale * (np.cos(t) - 2 * np.cos(2 * t))
    z = scale * (-np.sin(3 * t))
    return np.stack([x, y, z], axis=-1)

def generate_saw_cylinder(R=1.0, height=2.0, turns=5, step_fwd=11, step_bwd=-9, points_per_turn=100):
    """
    Generates the 'Saw' (Zig-Zag) geometry on a Cylinder.
    SST Metric: Maximizes Helicity and Shear at the reversal nodes.
    """
    total_points = turns * points_per_turn
    t = np.linspace(0, turns * 2 * np.pi, total_points)

    # 1. Base Cylinder Geometry
    x = R * np.cos(t)
    y = R * np.sin(t)

    # 2. The "Saw" Z-Profile
    # We simulate the Forward/Back motion by modulating the Z-height
    # purely as a function of the winding angle (t).
    # Net progress per cycle = (Fwd + Bwd).
    # We use a sawtooth wave function here for simulation.

    net_pitch = height / (turns * 2 * np.pi)
    saw_amplitude = (step_fwd - abs(step_bwd)) * 0.05 # Scale factor

    # Linear climb (The "Net" progress) + Sawtooth Oscillation
    z_linear = t * net_pitch
    z_wobble = saw_amplitude * np.sin(t * (step_fwd + abs(step_bwd))/2) # High freq zig-zag

    z = z_linear + z_wobble
    z = z - (height / 2) # Center it

    return np.stack([x, y, z], axis=-1)

# --- 6. Main Solver Class ---
class SSTSolver:
    def __init__(self, resolution=11, bounds=2.0):
        self.grid_N = resolution
        self.bounds = bounds
        self.setup_grid()

    def setup_grid(self):
        vals = np.linspace(-self.bounds, self.bounds, self.grid_N)
        self.X, self.Y, self.Z = np.meshgrid(vals, vals, vals, indexing='ij')
        self.grid_flat = np.stack([self.X.flatten(), self.Y.flatten(), self.Z.flatten()], axis=-1)
        self.dx = vals[1] - vals[0]

    def compute(self, params, geometry_type, analysis_mode):
        wires = []
        dipoles = []

        # 1. Build Geometry
        if "Rodin" in geometry_type:
            wires.append(generate_rodin_starship(
                R=params['rodin_R'], r=params['rodin_r'], num_turns=params['turns']))

        if "Trefoil" in geometry_type:
            wires.append(generate_trefoil(scale=1.2))

        if "Saw Cylinder" in geometry_type:
            wires.append(generate_saw_cylinder(
                R=params.get('rodin_R', 1.0),  # Reuse the 'R' slider
                height=3.0,
                turns=params.get('turns', 5),
                step_fwd=params.get('step_fwd', 11),
                step_bwd=params.get('step_bwd', -9),
                points_per_turn=100
            ))

        if "Dipole" in geometry_type:
            # Bottom Ring
            p1, m1 = generate_dipole_ring(params['ring_R'], params['n_mag'], z_offset=-0.75)
            dipoles.append((p1, m1))
            # Top Ring (Inverted)
            p2, m2 = generate_dipole_ring(params['ring_R'], params['n_mag'], z_offset=0.75, invert=True)
            dipoles.append((p2, m2))

        # 2. Compute Vectors (B or A)
        # We generally need B for most things, A for Helicity

        calc_A = (analysis_mode == 'Vector Potential (A)') or (analysis_mode == 'Helicity Density (h)')
        calc_B = True # Always needed for geometry ref or Gravity

        B_flat = np.zeros_like(self.grid_flat)
        A_flat = np.zeros_like(self.grid_flat)

        # --- Compute B ---
        if calc_B:
            for w in wires:
                if _HAS_SST_BINDINGS:
                    try: B_flat += np.array(sstbindings.biot_savart_velocity_grid(w, self.grid_flat))
                    except: B_flat += SSTGravity._numpy_wire_field(self.grid_flat, w, mode='B')
                else:
                    B_flat += SSTGravity._numpy_wire_field(self.grid_flat, w, mode='B')

            for (pos, mom) in dipoles:
                if _HAS_SST_BINDINGS:
                    try:
                        # Assuming binding returns tuple (Bx, By, Bz)
                        res = sstbindings.dipole_ring_field_grid(self.X, self.Y, self.Z, pos, mom)
                        B_flat += np.stack([r.flatten() for r in res], axis=-1)
                    except: B_flat += SSTGravity._numpy_dipole_field(self.grid_flat, pos, mom, mode='B')
                else:
                    B_flat += SSTGravity._numpy_dipole_field(self.grid_flat, pos, mom, mode='B')

        # --- Compute A ---
        if calc_A:
            for w in wires:
                if _HAS_SST_BINDINGS:
                    try:
                        res = sstbindings.biot_savart_vector_potential_grid(w, self.grid_flat, 1.0)
                        # Check if tuple or array
                        if isinstance(res, tuple): A_flat += np.stack([r.flatten() for r in res], axis=-1)
                        else: A_flat += np.array(res)
                    except: A_flat += SSTGravity._numpy_wire_field(self.grid_flat, w, mode='A')
                else:
                    A_flat += SSTGravity._numpy_wire_field(self.grid_flat, w, mode='A')

            for (pos, mom) in dipoles:
                # No binding for dipole A usually, use fallback
                A_flat += SSTGravity._numpy_dipole_field(self.grid_flat, pos, mom, mode='A')

        # 3. Post-Process Metrics
        scalar_field = None
        vector_field = B_flat # Default visualization vector

        if analysis_mode == 'Gravity Dilation (G)':
            # Frequency coupling
            omega = 2 * np.pi * params['freq_hz']
            # Calculate G
            G = SSTGravity.compute_gravity_dilation(B_flat, omega, B_sat=params['B_sat'])
            scalar_field = 1.0 - G # Plot "Modification Factor" (0=Normal, 1=Max)
            vector_field = B_flat

        elif analysis_mode == 'Helicity Density (h)':
            h = SSTGravity.compute_helicity_density(A_flat, B_flat)
            scalar_field = h
            vector_field = B_flat

        elif analysis_mode == 'Vector Potential (A)':
            scalar_field = np.linalg.norm(A_flat, axis=-1)
            vector_field = A_flat

        else: # Magnetic Field B
            scalar_field = np.linalg.norm(B_flat, axis=-1)
            vector_field = B_flat

        return vector_field, scalar_field, wires, dipoles

# --- 7. Visualization & GUI ---

# Parameters
params = {
    'rodin_R': 1.0, 'rodin_r': 0.4, 'turns': 6,
    'ring_R': 0.6, 'n_mag': 12,
    'freq_hz': 1e6, 'B_sat': 50.0,
    'step_fwd': 11, 'step_bwd': -9  # Saw geometry parameters
}

solver = SSTSolver(resolution=11) # Low res for realtime interactivity

# Layout
fig = plt.figure(figsize=(13, 8))
ax = fig.add_subplot(111, projection='3d')
plt.subplots_adjust(left=0.35, right=0.95, bottom=0.1)

# GUI State
state = {
    'geom': 'Rodin + Dipoles',
    'field': 'Magnetic Field (B)'
}

def update_viz(val=None):
    t0 = time.time()
    vecs, scalars, wires, dipoles = solver.compute(params, state['geom'], state['field'])

    ax.clear()

    # 1. Geometry
    for w in wires:
        ax.plot(w[:,0], w[:,1], w[:,2], c='magenta', lw=2, alpha=0.6, label='Coil')
    for (pos, mom) in dipoles:
        ax.quiver(pos[:,0], pos[:,1], pos[:,2],
                  mom[:,0], mom[:,1], mom[:,2], length=0.25, color='cyan', alpha=0.5)

    # 2. Fields
    # Mask low values to reduce clutter
    mag = np.linalg.norm(vecs, axis=-1)
    threshold = np.percentile(mag, 25)
    mask = mag > threshold

    X = solver.grid_flat[mask, 0]
    Y = solver.grid_flat[mask, 1]
    Z = solver.grid_flat[mask, 2]
    U = vecs[mask, 0]
    V = vecs[mask, 1]
    W = vecs[mask, 2]
    C = scalars[mask]

    # Normalize vectors for quiver size consistency
    # (Color carries the magnitude info)
    U_n = U / (mag[mask] + 1e-9)
    V_n = V / (mag[mask] + 1e-9)
    W_n = W / (mag[mask] + 1e-9)

    cmap_map = {
        'Magnetic Field (B)': 'plasma',
        'Vector Potential (A)': 'viridis',
        'Helicity Density (h)': 'coolwarm',
        'Gravity Dilation (G)': 'inferno'
    }

    ax.quiver(X, Y, Z, U_n, V_n, W_n, length=0.25, normalize=True,
              cmap=cmap_map.get(state['field'], 'viridis'), array=C)

    # Labels
    ax.set_title(f"SST Visualizer: {state['field']}\nGeom: {state['geom']}")
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    ax.set_xlim(-2,2); ax.set_ylim(-2,2); ax.set_zlim(-2,2)

    if IN_COLAB:
        fig.canvas.draw_idle()
    else:
        plt.draw()

# --- Widgets ---

# Geometry Selection
ax_geom = plt.axes([0.02, 0.75, 0.25, 0.15])
rad_geom = RadioButtons(ax_geom, ('Rodin Only', 'Rodin + Dipoles', 'Trefoil', 'Saw Cylinder'), active=1)
def set_geom(l): state['geom'] = l; update_viz()
rad_geom.on_clicked(set_geom)
ax_geom.set_title("Geometry Topology")

# Field Selection
ax_field = plt.axes([0.02, 0.50, 0.25, 0.20])
rad_field = RadioButtons(ax_field, ('Magnetic Field (B)', 'Vector Potential (A)',
                                    'Helicity Density (h)', 'Gravity Dilation (G)'), active=0)
def set_field(l): state['field'] = l; update_viz()
rad_field.on_clicked(set_field)
ax_field.set_title("SST Metric")

# Inputs
ax_t1 = plt.axes([0.15, 0.40, 0.10, 0.05])
tb_turns = TextBox(ax_t1, "Turns: ", initial=str(params['turns']))
def sub_turns(t):
    try: params['turns'] = int(t); update_viz()
    except: pass
tb_turns.on_submit(sub_turns)

ax_t2 = plt.axes([0.15, 0.34, 0.10, 0.05])
tb_freq = TextBox(ax_t2, "Freq (Hz): ", initial="1e6")
def sub_freq(t):
    try: params['freq_hz'] = float(t); update_viz()
    except: pass
tb_freq.on_submit(sub_freq)

# --- Initial Run ---
print("[SST] Starting visualizer...")
update_viz()
plt.show()