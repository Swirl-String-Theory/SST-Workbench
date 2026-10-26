import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SST Gravity Lab (Interactive)",
    page_icon="🌀",
    layout="wide"
)

# --- SST CANONICAL CONSTANTS [2025-11-21] ---
RHO_F   = 7.0e-7          # Effective fluid density [kg m^-3]
C_SWIRL = 1.09384563e6    # Characteristic swirl speed [m s^-1]
MU_0    = 4 * np.pi * 1e-7

# --- PHYSICS ENGINE ---

class SSTGravity:
    """
    SST Physics Engine for Gravity Modification Metrics.
    """
    @staticmethod
    def compute_dilation(B_vec, omega, B_sat):
        """
        Calculates G_local. Returns modification factor (0.0 to 1.0).
        """
        B_mag = np.linalg.norm(B_vec, axis=-1)
        freq_scale = np.log10(omega) if omega > 1.0 else 0.0
        coupling = (B_mag / B_sat) * freq_scale
        mod_factor = np.square(coupling)
        return np.clip(mod_factor, 0.0, 1.0)

@st.cache_data(show_spinner=False)
def generate_rodin_coil_cached(R, r, num_turns, num_points, phase_shift):
    theta = np.linspace(0, num_turns * 2 * np.pi, num_points)
    phi = (2 + 2/5) * theta + phase_shift
    x = (R + r * np.cos(phi)) * np.cos(theta)
    y = (R + r * np.cos(phi)) * np.sin(theta)
    z = r * np.sin(phi)
    return np.stack([x, y, z], axis=1)

@st.cache_data(show_spinner=False)
def compute_field_cached(grid_coords, coil_points, I):
    gx, gy, gz = grid_coords
    points = np.stack([gx.ravel(), gy.ravel(), gz.ravel()], axis=1)

    dl = np.diff(coil_points, axis=0)
    mid = (coil_points[:-1] + coil_points[1:]) / 2

    r_vec = points[:, np.newaxis, :] - mid[np.newaxis, :, :]
    dist = np.linalg.norm(r_vec, axis=2)
    dist[dist < 1e-9] = 1e-9

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
freq_mhz = st.sidebar.slider("Resonance Freq (MHz)", 0.1, 50.0, 3.5, 0.1)
omega = 2 * np.pi * (freq_mhz * 1e6)
current = st.sidebar.slider("Coil Current (Amps)", 100, 5000, 2000, 100)
b_sat   = st.sidebar.number_input("B-Saturation Limit (Tesla)", 1.0, 100.0, 5.0)

st.sidebar.markdown("### 3. Visualization")
res = st.sidebar.slider("Grid Resolution", 8, 18, 12, 1) # Keep slightly lower for browser performance
cone_scale = st.sidebar.slider("Vector Scale", 0.1, 2.0, 0.5, 0.1)
opacity = st.sidebar.slider("Field Opacity", 0.1, 1.0, 0.7, 0.1)

# --- MAIN APP LOGIC ---

st.title("Swirl String Theory: Interactive Gravity Lab")
st.markdown(f"""
**Protocol:** Rodin Coil Topology
* **Swirl Velocity:** $v_{{\circlearrowleft}} = {C_SWIRL:.4e}$ m/s
* **Visual:** Color indicates Gravity Dilation ($1-G$), Orientation indicates Magnetic Field ($B$).
""")

# 1. Generate Coils
coils = []
points_per_coil = 400
offsets = [0, 2*np.pi/3, -2*np.pi/3]
for off in offsets:
    c = generate_rodin_coil_cached(R_major, r_minor, turns, points_per_coil, off)
    coils.append(c)

# 2. Setup Grid
bounds = 2.0
x = np.linspace(-bounds, bounds, res)
y = np.linspace(-bounds, bounds, res)
z = np.linspace(-bounds, bounds, res)
X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

# 3. Compute Physics
with st.spinner("Simulating Vector Fields..."):
    B_total_flat = np.zeros((X.size, 3))
    grid_tuple = (X, Y, Z)

    for coil in coils:
        B_part = compute_field_cached(grid_tuple, coil, current)
        B_total_flat += B_part

    Bx = B_total_flat[:, 0].reshape(X.shape)
    By = B_total_flat[:, 1].reshape(X.shape)
    Bz = B_total_flat[:, 2].reshape(X.shape)
    B_vec = np.stack([Bx, By, Bz], axis=-1)

    mod_factor = SSTGravity.compute_dilation(B_vec, omega, b_sat)

# 4. Interactive Plotly Visualization
col1, col2 = st.columns([3, 1])
with col1:
    fig = go.Figure()

    # A. Add Coils (Lines)
    coil_colors = ['#FF0000', '#00FF00', '#0000FF']
    for i, coil in enumerate(coils):
        fig.add_trace(go.Scatter3d(
            x=coil[:,0], y=coil[:,1], z=coil[:,2],
            mode='lines',
            line=dict(color=coil_colors[i], width=4),
            name=f'Phase {i+1}',
            hoverinfo='none'
        ))

    # B. Add Vector Field (Dynamic Scaling)
    mask = mod_factor > 0.001

    if np.any(mask):
        Xf, Yf, Zf = X[mask], Y[mask], Z[mask]
        Uf, Vf, Wf = Bx[mask], By[mask], Bz[mask]

        # 1. Calculate Field Metrics
        # We need the max magnitude to scale the arrows down
        B_mag = np.linalg.norm(np.stack([Uf, Vf, Wf], axis=-1), axis=-1)
        max_B = np.max(B_mag)

        # 2. Determine Visual Scale
        # We want the biggest arrow to be roughly 30% of a grid cell
        grid_spacing = (2 * bounds) / res
        target_arrow_size = grid_spacing * cone_scale

        # 3. Calculate sizeref
        # In 'scaled' mode: DisplaySize = Magnitude * sizeref
        # Therefore: sizeref = TargetSize / MaxMagnitude
        dynamic_sizeref = target_arrow_size / max_B

        # 4. Extract Gravity Data for Hover
        G_val = mod_factor[mask]

        fig.add_trace(go.Cone(
            x=Xf.flatten(),
            y=Yf.flatten(),
            z=Zf.flatten(),

            # PASS REAL VECTORS (Preserves Color Gradient)
            u=Uf.flatten(),
            v=Vf.flatten(),
            w=Wf.flatten(),

            # SCALE DYNAMICALLY (Fixes Huge Arrows)
            sizemode="scaled",
            sizeref=dynamic_sizeref,

            # Visuals
            colorscale='Inferno',
            colorbar=dict(title='B-Field (T)'),
            opacity=opacity,
            name='Field Vectors',

            # Hover Data
            customdata=np.stack((G_val, B_mag), axis=-1),
            hovertemplate='<b>G-Mod (1-G):</b> %{customdata[0]:.3f}<br><b>B-Field:</b> %{customdata[1]:.2f} T<extra></extra>'
        ))
    else:
        st.warning("Field too weak to render. Try increasing current.")

    # Layout Styling
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-bounds, bounds], showbackground=False, title='X'),
            yaxis=dict(range=[-bounds, bounds], showbackground=False, title='Y'),
            zaxis=dict(range=[-bounds, bounds], showbackground=False, title='Z'),
            aspectmode='cube'
        ),
        margin=dict(r=0, l=0, b=0, t=0),
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(yanchor="top", y=0.9, xanchor="left", x=0.1)
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Metrics")
    max_b = np.max(np.linalg.norm(B_vec, axis=-1))
    max_mod = np.max(mod_factor)

    st.metric("Peak B-Field", f"{max_b:.2f} T")
    st.metric("Max G-Modification", f"{max_mod*100:.1f} %")

    st.markdown("---")
    st.write("**Interaction Controls:**")
    st.write("🖱️ **Left Click:** Rotate")
    st.write("🖱️ **Right Click:** Pan")
    st.write("🖱️ **Scroll:** Zoom")
    st.write("👁️ **Hover:** See exact Tesla/Gravity values")

    st.markdown("---")
    if max_mod > 0.95:
        st.error("CRITICAL: Vacuum Breakdown")
    elif max_mod > 0.5:
        st.warning("WARNING: Time Dilation Active")
    else:
        st.success("STABLE: Standard Metric")