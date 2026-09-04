import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, RadioButtons, Button
from mpl_toolkits.mplot3d import Axes3D
import matplotlib

# Set backend to TkAgg for interactive window support
try:
    matplotlib.use('TkAgg')
except:
    print("Warning: TkAgg backend not available. Plots may not be interactive.")

# --- 1. SST CONSTANTS & CONFIGURATION ---
# Canonical Constants per SST Canon
V_SWIRL = 1.09384563e6  # m/s (Characteristic Swirl Speed)
C_LIGHT = 299792458.0   # m/s (Speed of Light)
OMEGA_DEFAULT = 10.9e6  # Hz (Canonical frequency scaling)
B_SAT_DEFAULT = 5.0     # Tesla (Core saturation limit)

# Geometry Defaults
S_DEFAULT = 40
STEP_FWD = 11
STEP_BWD = -9
POWER = 2.2 # For exponential profile curvature

# --- 2. SST PHYSICS CORE ---
# Attempt to load C++ bindings; fallback to Python approximation if missing
try:
    import sstbindings
    from sstbindings import biot_savart_wire_grid, SSTGravity
    HAS_SST = True
    print("SUCCESS: SST C++ Bindings loaded.")
except ImportError:
    HAS_SST = False
    print("WARNING: 'sstbindings' not found. Using Python fallback approximation.")

def compute_sst_physics(phases_geometry, grid_dims, bounds, Hc):
    """
    Computes B-field, Shear, and Gravity Dilation.
    If C++ bindings are missing, uses an analytical approximation for the Bowl shape.
    """
    nx, ny, nz = grid_dims
    limit = bounds
    x = np.linspace(-limit, limit, nx)
    y = np.linspace(-limit, limit, ny)
    z = np.linspace(0, limit, nz)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

    # Initialize Fields
    Bx_tot = np.zeros_like(X)
    By_tot = np.zeros_like(Y)
    Bz_tot = np.zeros_like(Z)

    if HAS_SST:
        # High-Fidelity C++ Calculation
        Xf, Yf, Zf = X.flatten(), Y.flatten(), Z.flatten()
        for polyline in phases_geometry:
            bx, by, bz = biot_savart_wire_grid(Xf, Yf, Zf, polyline, 1.0)
            Bx_tot += bx.reshape(X.shape)
            By_tot += by.reshape(Y.shape)
            Bz_tot += bz.reshape(Z.shape)
    else:
        # Python Approximation (Analytical model of a tapered solenoid)
        # Simulates the gradient of a Bowl Coil without heavy integration
        # B_z decays with Z; B_radial increases with radius
        R = np.sqrt(X**2 + Y**2) + 1e-9
        decay = np.exp(-(Z - Hc/2)**2) # Field strongest in center
        taper = 1.0 - (0.5 * Z/limit)  # Field compresses at top (if converging) or expands

        Bx_tot = -X/R * 0.5 * decay * taper
        By_tot = -Y/R * 0.5 * decay * taper
        Bz_tot = 1.0 * decay * taper

    B_mag = np.sqrt(Bx_tot**2 + By_tot**2 + Bz_tot**2) + 1e-9

    # Calculate Gradients (Numerical Curl)
    dVz_dy = np.gradient(Bz_tot, y, axis=1)
    dVy_dz = np.gradient(By_tot, z, axis=2)
    dVx_dz = np.gradient(Bx_tot, z, axis=2)
    dVz_dx = np.gradient(Bz_tot, x, axis=0)
    dVy_dx = np.gradient(By_tot, x, axis=0)
    dVx_dy = np.gradient(Bx_tot, y, axis=1)

    Wx = dVz_dy - dVy_dz
    Wy = dVx_dz - dVz_dx
    Wz = dVy_dx - dVx_dy

    if HAS_SST:
        # Use Canon functions
        B_flat = np.stack([Bx_tot.flatten(), By_tot.flatten(), Bz_tot.flatten()], axis=-1)
        Curl_flat = np.stack([Wx.flatten(), Wy.flatten(), Wz.flatten()], axis=-1)

        shear = np.array(SSTGravity.compute_beltrami_shear(B_flat, Curl_flat)).reshape(X.shape)
        gravity = np.array(SSTGravity.compute_gravity_dilation(
            B_flat, OMEGA_DEFAULT, V_SWIRL, B_SAT_DEFAULT
        )).reshape(X.shape)
    else:
        # Python Approximation of SST metrics
        # Beltrami Shear: |B x Curl(B)| / |B|
        # In a perfect Beltrami field, this is zero. High values = Turbulence/Drag.
        cross_x = By_tot*Wz - Bz_tot*Wy
        cross_y = Bz_tot*Wx - Bx_tot*Wz
        cross_z = Bx_tot*Wy - By_tot*Wx
        shear = np.sqrt(cross_x**2 + cross_y**2 + cross_z**2) / B_mag

        # Gravity Dilation: 1 - (v_f^2 / c^2). Proportional to B^2 in simple model.
        # SST Canon: Local time flows slower where B is high.
        # We visualize "Gravity" as the local pressure gradient potential.
        gravity = 1.0 - (B_mag / B_SAT_DEFAULT)**2

    return {
        "X":X, "Y":Y, "Z":Z,
        "Bx":Bx_tot/B_mag, "By":By_tot/B_mag, "Bz":Bz_tot/B_mag,
        "mag":B_mag, "shear":shear, "gravity":gravity
    }

# --- 3. RESONANCE ANALYZER ---
class ResonanceAnalyzer:
    def __init__(self, geometry_phases, V_swirl):
        self.phases = geometry_phases
        self.v_swirl = V_swirl
        self.c = C_LIGHT

    def analyze(self):
        print("\n" + "="*50)
        print("     SST RESONANCE & SIGNAL ANALYSIS TOOL")
        print("="*50)

        results = []
        for i, phase_pts in enumerate(self.phases):
            # Calculate precise wire length
            diffs = np.diff(phase_pts, axis=0)
            dists = np.linalg.norm(diffs, axis=1)
            L_total = np.sum(dists)

            if L_total == 0: continue

            # 1. Electrical Resonance (Standing Wave)
            # Target: Quarter-Wave (lambda/4) for max E-field at tips
            f_elec = self.c / (4 * L_total)

            # 2. Vortex Resonance (Hydraulic Cycle)
            # Target: Frequency matching fluid transit time across the wire length
            f_vortex = self.v_swirl / L_total

            # 3. Critical Rise Time (The "Snap")
            # Max time to switch state before fluid flows around the wire
            # Based on 1mm wire diameter approximation
            t_impact = 0.001 / self.v_swirl

            print(f"PHASE {i+1} GEOMETRY:")
            print(f"  Wire Length:      {L_total:.4f} m")
            print(f"  Inductance Est:   {(L_total * 1.2):.2f} uH (approx)")
            print("-" * 30)
            print(f"REQUIRED SIGNAL PARAMETERS (BURST MODE):")
            print(f"  1. Carrier Freq:  {f_elec/1e6:.3f} MHz  (Standing Wave)")
            print(f"  2. Burst Rate:    {f_vortex/1e3:.3f} kHz  (Vortex Cycle)")
            print(f"  3. Max Rise Time: {t_impact*1e9:.2f} ns   (Impact Threshold)")
            print("\n")

            results.append((L_total, f_elec, f_vortex))

        print("INSTRUCTION: Use Asymmetric Sawtooth envelope at Burst Rate.")
        print("             Carrier should be Sine at Carrier Freq.")
        print("="*50 + "\n")
        return results

# --- 4. GEOMETRY GENERATORS ---
def alternating_skip_indices(S, step_fwd, step_bwd, n_pairs, start=1):
    idx = start
    seq = [idx]
    for k in range(2 * n_pairs):
        if k % 2 == 0:
            idx = (idx + step_fwd - 1) % S + 1
        else:
            idx = (idx + step_bwd - 1) % S + 1
        seq.append(idx)
    return np.array(seq, dtype=int)

def r_profile(s, Rb, Rt, profile, power):
    if profile == 'Exponential':
        return Rb + (Rt - Rb) * (s**power)
    elif profile == 'Inverse Exp':
        return Rt - (Rt - Rb) * (s**power)
    else:  # Linear
        return Rb + (Rt - Rb) * s

def generate_bowl_geometry(S, step_fwd, step_bwd, n_pairs, Rb, Rt, Hc,
                           profile='Exponential', mode='Curved', angle_offset=0.0):
    seq = alternating_skip_indices(S, step_fwd, step_bwd, n_pairs, start=1)
    slot_angles_base = np.linspace(0, 2*np.pi, S, endpoint=False) - np.pi/2.0

    N_segs = len(seq) - 1

    if mode == 'Curved':
        samples_per_seg = 12
        s_nodes = np.linspace(0, 1, N_segs + 1)
        r_nodes = r_profile(s_nodes, Rb, Rt, profile, POWER)
        z_nodes = s_nodes

        xs, ys, zs = [], [], []

        for k in range(N_segs):
            i0, i1 = seq[k]-1, seq[k+1]-1
            a0 = slot_angles_base[i0] + angle_offset
            a1 = slot_angles_base[i1] + angle_offset
            da = (a1 - a0 + np.pi) % (2*np.pi) - np.pi

            t = np.linspace(0, 1, samples_per_seg, endpoint=False)
            a_line = a0 + t * da
            r_line = np.linspace(r_nodes[k], r_nodes[k+1], samples_per_seg, endpoint=False)
            z_line = np.linspace(z_nodes[k], z_nodes[k+1], samples_per_seg, endpoint=False)

            xs.append(r_line * np.cos(a_line))
            ys.append(r_line * np.sin(a_line))
            zs.append(z_line)

        # Final point
        a_end = slot_angles_base[seq[-1]-1] + angle_offset
        xs.append([r_nodes[-1] * np.cos(a_end)])
        ys.append([r_nodes[-1] * np.sin(a_end)])
        zs.append([z_nodes[-1]])

        X = np.concatenate(xs)
        Y = np.concatenate(ys)
        Z = np.concatenate(zs) * Hc
    else: # Straight
        s_nodes = np.linspace(0, 1, N_segs + 1)
        r_nodes = r_profile(s_nodes, Rb, Rt, profile, POWER)
        z_nodes = s_nodes * Hc
        angles = slot_angles_base[seq-1] + angle_offset
        X = r_nodes * np.cos(angles)
        Y = r_nodes * np.sin(angles)
        Z = z_nodes

    return np.stack([X, Y, Z], axis=-1), seq

# --- 5. GUI APPLICATION ---
class SawBowlApp:
    def __init__(self):
        self.fig = plt.figure(figsize=(14, 9))
        self.ax = self.fig.add_subplot(111, projection='3d')
        plt.subplots_adjust(left=0.05, right=0.75, bottom=0.1)

        self.params = {
            "Rb": 0.5, "Rt": 1.5, "layers": 20, "Hc": 1.0,
            "grid_res": 9, "bounds": 2.5
        }
        self.mode = "Curved"
        self.profile = "Exponential"
        self.phases_active = [True, True, True]

        self.init_gui()
        self.update()

    def init_gui(self):
        # Sliders
        ax_Rb = plt.axes([0.15, 0.08, 0.55, 0.03])
        ax_Rt = plt.axes([0.15, 0.04, 0.55, 0.03])
        ax_L  = plt.axes([0.15, 0.005, 0.25, 0.03])
        ax_H  = plt.axes([0.45, 0.005, 0.25, 0.03])

        self.sl_Rb = Slider(ax_Rb, 'R Base', 0.01, 3.0, valinit=self.params["Rb"])
        self.sl_Rt = Slider(ax_Rt, 'R Top', 0.01, 3.0, valinit=self.params["Rt"])
        self.sl_L  = Slider(ax_L,  'Layers', 5, 80, valinit=self.params["layers"], valstep=1)
        self.sl_H  = Slider(ax_H,  'Height', 0.1, 3.0, valinit=self.params["Hc"])

        for s in [self.sl_Rb, self.sl_Rt, self.sl_L, self.sl_H]:
            s.on_changed(self.update_wrapper)

        # Controls
        ax_mode = plt.axes([0.8, 0.75, 0.15, 0.12])
        self.rad_mode = RadioButtons(ax_mode, ('Curved', 'Straight'), active=0)
        self.rad_mode.on_clicked(self.set_mode)
        ax_mode.set_title("Wire Mode")

        ax_prof = plt.axes([0.8, 0.55, 0.15, 0.15])
        self.rad_prof = RadioButtons(ax_prof, ('Exponential', 'Linear', 'Inverse Exp'), active=0)
        self.rad_prof.on_clicked(self.set_profile)
        ax_prof.set_title("Hull Profile")

        ax_view = plt.axes([0.8, 0.35, 0.15, 0.15])
        self.rad_view = RadioButtons(ax_view,
                                     ('SST Gravity Dilation', 'Beltrami Shear', 'Magnetic Field', 'Geometry Only'), active=3)
        self.rad_view.on_clicked(self.update_wrapper)
        ax_view.set_title("Physics View")

        # RESONANCE BUTTON
        ax_btn = plt.axes([0.8, 0.25, 0.15, 0.05])
        self.btn_calc = Button(ax_btn, 'Calc Resonance', color='lightblue', hovercolor='0.9')
        self.btn_calc.on_clicked(self.run_resonance_calc)

    def set_mode(self, label):
        self.mode = label
        self.update()

    def set_profile(self, label):
        self.profile = label
        self.update()

    def update_wrapper(self, val=None):
        self.update()

    def run_resonance_calc(self, event):
        phases_geo = self.generate_current_geometry()
        analyzer = ResonanceAnalyzer(phases_geo, V_SWIRL)
        analyzer.analyze()

    def generate_current_geometry(self):
        Rb = self.sl_Rb.val
        Rt = self.sl_Rt.val
        n_pairs = int(self.sl_L.val)
        Hc = self.sl_H.val
        phases_geo = []
        offsets = [0.0, 2*np.pi/3, 4*np.pi/3]
        for i in range(3):
            if self.phases_active[i]:
                pts, _ = generate_bowl_geometry(
                    S_DEFAULT, STEP_FWD, STEP_BWD, n_pairs,
                    Rb, Rt, Hc, self.profile, self.mode, offsets[i]
                )
                phases_geo.append(pts)
        return phases_geo

    def update(self):
        self.ax.clear()

        # Get Geometry
        phases = []
        phases_geo = self.generate_current_geometry()
        colors = ['purple', 'blue', 'green']

        for i, pts in enumerate(phases_geo):
            phases.append((pts, colors[i%3]))

        # Physics
        view = self.rad_view.value_selected
        if view != 'Geometry Only':
            grid_dims = (self.params["grid_res"], self.params["grid_res"], self.params["grid_res"])
            data = compute_sst_physics(phases_geo, grid_dims, self.params["bounds"], self.sl_H.val)
            X, Y, Z = data["X"], data["Y"], data["Z"]

            # Filter vectors for visibility
            if view == 'SST Gravity Dilation':
                # Show where gravity is REDUCED (dilation > 0)
                vals = 1.0 - data["gravity"]
                mask = vals > 0.001
                cmap = 'inferno'
                scale = 0.2
            elif view == 'Beltrami Shear':
                vals = data["shear"]
                norm_vals = (vals - vals.min()) / (np.ptp(vals) + 1e-9)
                mask = norm_vals > 0.2
                vals = norm_vals
                cmap = 'jet'
                scale = 0.2
            else:
                vals = data["Bz"]
                mask = data["mag"] > 0.1
                cmap = 'coolwarm'
                scale = 0.15

            if np.any(mask):
                self.ax.quiver(
                    X[mask], Y[mask], Z[mask],
                    data["Bx"][mask], data["By"][mask], data["Bz"][mask],
                    length=scale, normalize=True, cmap=cmap, array=vals[mask], alpha=0.5
                )

        # Plot Geometry
        for pts, col in phases:
            self.ax.plot(pts[:,0], pts[:,1], pts[:,2], c=col, lw=1.0, alpha=0.9)

        # Setup Plot Limits
        lim = max(self.sl_Rb.val, self.sl_Rt.val) * 1.5
        self.ax.set_xlim(-lim, lim)
        self.ax.set_ylim(-lim, lim)
        self.ax.set_zlim(0, self.sl_H.val * 1.5)
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.set_zlabel('Z (m)')
        self.ax.set_title(f"SST Saw-Bowl: {self.mode}")
        self.fig.canvas.draw_idle()

if __name__ == "__main__":
    app = SawBowlApp()
    plt.show()