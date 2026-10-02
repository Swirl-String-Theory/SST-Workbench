import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SST DomeTrap Simulator",
    page_icon="🧲",
    layout="wide"
)

# --- SST CANONICAL CONSTANTS [2025-11-21] ---
# v_swirl = 1.09384563e6 m/s
MU_0 = 4 * np.pi * 1e-7

# --- HELPER: CACHED GEOMETRY ---
@st.cache_data(show_spinner=False)
def generate_dome_coils_cached(radius, gap, layers, mode):
    """
    Generates the spiral geometry for the Dome Trap.
    Cached to prevent recalculation on every frame.
    """
    def make_spiral(z_start, z_end, z_offset, chirality):
        points = 500
        t = np.linspace(0, 1, points)

        # Spherical cap projection
        z_local = z_start + (z_end - z_start) * t
        r_local = np.sqrt(np.clip(radius**2 - z_local**2, 0, None))

        total_angle = 2 * np.pi * layers
        theta = total_angle * t * chirality

        x = r_local * np.cos(theta)
        y = r_local * np.sin(theta)
        z = z_local + z_offset
        return np.stack([x, y, z], axis=-1)

    # Bottom Dome (South)
    pts_bot = make_spiral(-radius, -gap/2.0, radius, 1)

    # Top Dome (North)
    # Mode 'Opposing' (Cusp) -> Chirality flipped (-1)
    chirality_top = -1 if mode == 'Opposing' else 1
    pts_top = make_spiral(radius, gap/2.0, -radius, chirality_top)

    return pts_bot, pts_top

# --- HELPER: PHYSICS ENGINE ---
@st.cache_data(show_spinner=False)
def compute_dome_physics(grid_params, coil_data, current):
    """
    Optimized Biot-Savart Calculation using Numpy vectorization.
    """
    L, res = grid_params
    pts_bot, pts_top = coil_data

    # Setup Grid
    x = np.linspace(-L, L, res)
    X, Y, Z = np.meshgrid(x, x, x, indexing='ij')

    # Containers
    Bx_tot = np.zeros_like(X)
    By_tot = np.zeros_like(Y)
    Bz_tot = np.zeros_like(Z)

    all_coils = [pts_bot, pts_top]

    # Flatten grid for vectorization
    target = np.stack([X.flatten(), Y.flatten(), Z.flatten()], axis=1)
    mu0_4pi = 1e-7 * current

    for polyline in all_coils:
        p_starts = polyline[:-1]
        p_ends = polyline[1:]
        dl = p_ends - p_starts
        mid = (p_starts + p_ends) / 2

        # Loop through segments
        for i in range(len(dl)):
            d_vec = dl[i]
            pos = mid[i]

            rx = target[:, 0] - pos[0]
            ry = target[:, 1] - pos[1]
            rz = target[:, 2] - pos[2]

            r_sq = rx**2 + ry**2 + rz**2
            # Add small epsilon to prevent singularity
            r_cubed = (r_sq**1.5) + 1e-9

            cross_x = d_vec[1]*rz - d_vec[2]*ry
            cross_y = d_vec[2]*rx - d_vec[0]*rz
            cross_z = d_vec[0]*ry - d_vec[1]*rx

            factor = mu0_4pi / r_cubed

            Bx_tot += (cross_x * factor).reshape(X.shape)
            By_tot += (cross_y * factor).reshape(Y.shape)
            Bz_tot += (cross_z * factor).reshape(Z.shape)

    return X, Y, Z, Bx_tot, By_tot, Bz_tot

# --- MAIN APP ---

st.sidebar.title("🧲 DomeTrap Controls")

with st.sidebar.form("sim_params"):
    st.markdown("### Geometry")
    dome_radius = st.slider("Dome Radius (m)", 0.1, 0.5, 0.20, 0.01)
    dome_gap    = st.slider("Central Gap (m)", 0.01, 0.3, 0.1, 0.01)
    dome_layers = st.slider("Winding Layers", 5, 50, 20, 1)
    dome_mode   = st.selectbox("Magnetic Mode", ["Opposing", "Attracting"], index=0)

    st.markdown("### Physics")
    current = st.number_input("Current (Amps)", 100.0, 5000.0, 2000.0, 100.0)
    grid_res = st.slider("Grid Resolution", 10, 25, 15, 1) # Cap at 25 for browser perf
    bounds = st.slider("Sim Bounds (m)", 0.1, 1.0, 0.3, 0.05)

    st.markdown("### Visualization")
    # Separate scaling for Vector Cones vs Tension Cloud
    vector_scale = st.slider("Vector Size", 0.1, 2.0, 0.5, 0.1)
    cloud_opacity = st.slider("Tension Cloud Opacity", 0.1, 1.0, 0.2, 0.05)

    run_sim = st.form_submit_button("Run Simulation")

st.title("SST DomeTrap: Vacuum Stress Analyzer")
st.markdown("""
**System:** Contra-Rotating Hemispherical Dome (Quadrupole Trap).
* **Opposing Mode:** Creates a central **Null Point** ($B \\approx 0$).
* **Physics:** As magnetic pressure drops, **Vacuum Tension** ($T \\propto 1/|B|$) increases, maximizing the "swirl potential" of the local medium.
""")

if run_sim or 'first_run' not in st.session_state:
    st.session_state.first_run = True

    # 1. Generate Geometry
    pts_bot, pts_top = generate_dome_coils_cached(dome_radius, dome_gap, dome_layers, dome_mode)

    # 2. Compute Physics
    with st.spinner("Integrating Field Equations..."):
        X, Y, Z, Bx, By, Bz = compute_dome_physics((bounds, grid_res), (pts_bot, pts_top), current)

    # 3. Process Data
    # Calculate Magnitude
    B_mag = np.linalg.norm(np.stack([Bx, By, Bz], axis=-1), axis=-1)

    # Calculate Vacuum Tension (Inverse B)
    # Adding 0.5 constant prevents infinity and represents background ether pressure
    Vacuum_Tension = 1.0 / (B_mag + 0.5)

    # Normalize Tension 0-1 for visualization
    vt_max = np.max(Vacuum_Tension)
    vt_norm = Vacuum_Tension / vt_max

    # 4. Interactive Visualization
    col1, col2 = st.columns([3, 1])

    with col1:
        fig = go.Figure()

        # --- A. Plot Coils (Lines) ---
        phases = [(pts_bot, '#00CCFF'), (pts_top, '#FF3300')] # Cyan/Red
        for pts, col in phases:
            fig.add_trace(go.Scatter3d(
                x=pts[:,0], y=pts[:,1], z=pts[:,2],
                mode='lines',
                line=dict(color=col, width=4),
                name='Coil Winding',
                hoverinfo='none'
            ))

        # --- B. Plot Vacuum Tension Cloud (Scatter) ---
        # Mask: Only show regions of high tension (low B-field)
        cloud_mask = vt_norm > 0.6

        if np.any(cloud_mask):
            fig.add_trace(go.Scatter3d(
                x=X[cloud_mask].flatten(),
                y=Y[cloud_mask].flatten(),
                z=Z[cloud_mask].flatten(),
                mode='markers',
                marker=dict(
                    size=4,
                    color=vt_norm[cloud_mask].flatten(),
                    colorscale='Plasma', # Purple/Yellow is good for energy clouds
                    opacity=cloud_opacity,
                    colorbar=dict(title='Vacuum Tension', x=0.85)
                ),
                name='Vacuum Tension',
                hovertemplate='<b>Tension:</b> %{marker.color:.2f}<extra></extra>'
            ))

        # --- C. Plot B-Field Vectors (Dynamic Cones) ---
        # Subsample to keep scene clean (Plot every 2nd point)
        step = 1 if grid_res < 12 else 2

        # Slicing
        Xs = X[::step, ::step, ::step].flatten()
        Ys = Y[::step, ::step, ::step].flatten()
        Zs = Z[::step, ::step, ::step].flatten()
        Us = Bx[::step, ::step, ::step].flatten()
        Vs = By[::step, ::step, ::step].flatten()
        Ws = Bz[::step, ::step, ::step].flatten()
        Bs = B_mag[::step, ::step, ::step].flatten()

        # --- DYNAMIC SCALING LOGIC ---
        # 1. Get max B for scaling reference
        max_B_visible = np.max(Bs)

        # 2. Target size: ~30% of grid spacing
        grid_spacing = (2 * bounds) / grid_res
        target_size = grid_spacing * vector_scale

        # 3. Calculate sizeref
        # DisplaySize = Magnitude * sizeref
        # sizeref = TargetSize / MaxMagnitude
        dynamic_sizeref = target_size / (max_B_visible + 1e-9)

        fig.add_trace(go.Cone(
            x=Xs, y=Ys, z=Zs,
            u=Us, v=Vs, w=Ws,
            sizemode="scaled",
            sizeref=dynamic_sizeref,
            colorscale='Viridis',
            showscale=False, # We already have one colorbar for Tension
            opacity=0.6,
            name='B-Field',
            # Custom Hover Data
            customdata=Bs,
            hovertemplate='<b>B-Field:</b> %{customdata:.2f} T<extra></extra>'
        ))

        # Layout
        fig.update_layout(
            scene=dict(
                xaxis=dict(range=[-bounds, bounds], showbackground=False, title='X'),
                yaxis=dict(range=[-bounds, bounds], showbackground=False, title='Y'),
                zaxis=dict(range=[-bounds, bounds], showbackground=False, title='Z'),
                aspectmode='cube',
                bgcolor='rgba(0,0,0,0)'
            ),
            margin=dict(l=0, r=0, b=0, t=0),
            paper_bgcolor='rgba(0,0,0,0)',
            legend=dict(x=0, y=1)
        )

        st.plotly_chart(fig, use_container_width=True)

    # --- Metrics ---
    with col2:
        st.subheader("Data Probe")

        st.metric("Peak Tension", f"{vt_max:.4f} a.u.")
        st.metric("Min B (Trap Center)", f"{np.min(B_mag):.6f} T")
        st.metric("Max B (Surface)", f"{np.max(B_mag):.2f} T")

        st.markdown("---")
        if dome_mode == "Opposing":
            st.success("TRAP ACTIVE: Null Point Detected")
        else:
            st.info("FLOW STATE: Uniform Field")

        st.markdown("""
        **Controls:**
        * **Rotate:** Left-click drag
        * **Pan:** Right-click drag
        * **Zoom:** Scroll
        """)