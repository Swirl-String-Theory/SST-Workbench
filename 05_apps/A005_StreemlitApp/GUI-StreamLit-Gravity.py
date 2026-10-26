import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SST Gravity Lab",
    page_icon="🌀",
    layout="wide"
)

# --- SST CANONICAL CONSTANTS [2025-11-21] ---
# These are fixed physical constants from the SST Canon
RHO_F   = 7.0e-7          # Effective fluid density [kg m^-3]
C_SWIRL = 1.09384563e6    # Characteristic swirl speed [m s^-1]
MU_0    = 4 * np.pi * 1e-7

# --- PHYSICS ENGINE CLASSES ---

class SSTGravity:
    """
    SST Physics Engine for Gravity Modification Metrics.
    """
    @staticmethod
    def compute_dilation(B_vec, omega, B_sat):
        """
        Calculates G_local (Gravity Dilation Factor).
        Returns scalar field where 0.0 = Normal, 1.0 = Max Modification.
        """
        B_mag = np.linalg.norm(B_vec, axis=-1)

        # Logarithmic Frequency Scaling
        # SST Rule: Coupling requires f > 1 Hz
        freq_scale = np.log10(omega) if omega > 1.0 else 0.0

        # Coupling ratio
        coupling = (B_mag / B_sat) * freq_scale

        # G_local = 1 - coupling^2.
        # We return (1 - G_local) to visualize the MAGNITUDE of modification.
        # If coupling^2 > 1, modification is maxed at 1.0
        mod_factor = np.square(coupling)
        return np.clip(mod_factor, 0.0, 1.0)

@st.cache_data(show_spinner=False)
def generate_rodin_coil_cached(R, r, num_turns, num_points, phase_shift):
    """Generates geometric coordinates for a single Rodin coil phase."""
    theta = np.linspace(0, num_turns * 2 * np.pi, num_points)
    # Rodin star coil topology (Toroidal Knot)
    phi = (2 + 2/5) * theta + phase_shift

    x = (R + r * np.cos(phi)) * np.cos(theta)
    y = (R + r * np.cos(phi)) * np.sin(theta)
    z = r * np.sin(phi)
    return np.stack([x, y, z], axis=1)

@st.cache_data(show_spinner=False)
def compute_field_cached(grid_coords, coil_points, I):
    """Vectorized Biot-Savart Law (Cached for performance)."""
    # Unpack grid
    gx, gy, gz = grid_coords
    points = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)

    dl = np.diff(coil_points, axis=0)
    mid = (coil_points[:-1] + coil_points[1:]) / 2

    # Vectorized calculation
    r_vec = points[:, np.newaxis, :] - mid[np.newaxis, :, :]
    dist = np.linalg.norm(r_vec, axis=2)
    dist[dist < 1e-9] = 1e-9 # Singularity clamp

    cross = np.cross(dl[np.newaxis, :, :], r_vec)
    factor = (MU_0 * I) / (4 * np.pi * dist**3)[..., np.newaxis]

    B_flat = np.sum(cross * factor, axis=1)
    return B_flat

# --- SIDEBAR CONTROLS ---

st.sidebar.title("🌀 SST Parameter Control")

st.sidebar.markdown("### 1. Coil Geometry")
R_major = st.sidebar.slider("Major Radius (R)", 0.5, 3.0, 1.5, 0.1)
r_minor = st.sidebar.slider("Minor Radius (r)", 0.1, 1.5, 0.8, 0.1)
turns   = st.sidebar.slider("Winding Turns", 1, 24, 12, 1)

st.sidebar.markdown("### 2. Drive Parameters")
# Input frequency in MHz, convert to Hz
freq_mhz = st.sidebar.slider("Resonance Freq (MHz)", 0.1, 50.0, 3.5, 0.1)
omega = 2 * np.pi * (freq_mhz * 1e6)

current = st.sidebar.slider("Coil Current (Amps)", 100, 5000, 2000, 100)
b_sat   = st.sidebar.number_input("B-Saturation Limit (Tesla)", 1.0, 100.0, 5.0)

st.sidebar.markdown("### 3. Simulation Grid")
res = st.sidebar.slider("Grid Resolution", 8, 20, 12, 1, help="Higher = Slower but smoother")
bounds = st.sidebar.slider("View Bounds (m)", 1.0, 5.0, 2.0, 0.5)

# --- MAIN APP LOGIC ---

st.title("Swirl String Theory: Gravity Modification Lab")
st.markdown(f"""
**Simulation Protocol:** Rodin Coil Topology (Star Winding)
* **Canonical Swirl Velocity:** $v_{{\circlearrowleft}} = {C_SWIRL:.4e}$ m/s
* **Mechanism:** Frequency-modulated Magnetic Saturation
""")

# 1. Generate Coils
coils = []
points_per_coil = 600 # Fixed for performance
offsets = [0, 2*np.pi/3, -2*np.pi/3]

for off in offsets:
    c = generate_rodin_coil_cached(R_major, r_minor, turns, points_per_coil, off)
    coils.append(c)

# 2. Setup Grid
x = np.linspace(-bounds, bounds, res)
y = np.linspace(-bounds, bounds, res)
z = np.linspace(-bounds, bounds, res)
X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

# 3. Compute Physics
with st.spinner("Computing Vector Fields & SST Metrics..."):
    # Sum B-fields from all 3 phases
    B_total_flat = np.zeros((X.size, 3))
    grid_tuple = (X, Y, Z)

    for coil in coils:
        B_part = compute_field_cached(grid_tuple, coil, current)
        B_total_flat += B_part

    # Reshape
    Bx = B_total_flat[:, 0].reshape(X.shape)
    By = B_total_flat[:, 1].reshape(X.shape)
    Bz = B_total_flat[:, 2].reshape(X.shape)
    B_vec = np.stack([Bx, By, Bz], axis=-1)

    # SST Metric: Gravity Dilation
    # 0.0 = Normal G, 1.0 = Zero G
    mod_factor = SSTGravity.compute_dilation(B_vec, omega, b_sat)

# 4. Visualization
col1, col2 = st.columns([3, 1])

with col1:
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Plot Coils
    coil_colors = ['#FF0000', '#00FF00', '#0000FF']
    for i, coil in enumerate(coils):
        ax.plot(coil[:,0], coil[:,1], coil[:,2], color=coil_colors[i], lw=0.8, alpha=0.4)

    # Plot Field Vectors
    # Filter: Only show vectors where modification > 1%
    mask = mod_factor > 0.01

    if np.any(mask):
        # Subsample for cleaner plot if mask is too dense
        Xf, Yf, Zf = X[mask], Y[mask], Z[mask]
        Uf, Vf, Wf = Bx[mask], By[mask], Bz[mask]
        Cf = mod_factor[mask]

        q = ax.quiver(Xf, Yf, Zf, Uf, Vf, Wf,
                      length=bounds*0.15, normalize=True, cmap='inferno', array=Cf, alpha=0.8)
        cbar = fig.colorbar(q, ax=ax, shrink=0.5, pad=0.1)
        cbar.set_label('Gravity Modification Factor $(1 - G_{local})$')
    else:
        st.warning("Field intensity too low to trigger gravity modification. Increase Current or Frequency.")

    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    ax.set_xlim(-bounds, bounds)
    ax.set_ylim(-bounds, bounds)
    ax.set_zlim(-bounds, bounds)

    # Make background transparent for Streamlit dark mode integration
    fig.patch.set_alpha(0.0)
    ax.patch.set_alpha(0.0)

    st.pyplot(fig)

with col2:
    st.markdown("### Metrics")
    max_b = np.max(np.linalg.norm(B_vec, axis=-1))
    max_mod = np.max(mod_factor)

    st.metric("Peak B-Field", f"{max_b:.2f} T")
    st.metric("Max G-Modification", f"{max_mod*100:.1f} %")

    st.markdown("---")
    st.markdown("**SST Status:**")
    if max_mod > 0.95:
        st.success("CRITICAL: Vacuum Breakdown Imminent")
    elif max_mod > 0.5:
        st.warning("WARNING: Significant Time Dilation")
    else:
        st.info("STABLE: Standard Newtonian Metric")

    st.markdown("""
    **Theory Note:**
    $G_{local} = 1 - (\\frac{v_{ind}}{v_{\circlearrowleft}})^2$
    
    Where $v_{ind} \propto B \cdot \log(\omega)$
    """)