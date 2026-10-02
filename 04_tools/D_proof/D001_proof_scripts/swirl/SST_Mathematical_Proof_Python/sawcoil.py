
# streamlit run coil_streamlit_app.py
# -------------------------------------------------------
# 3-Phase Polygonal Coil Visualizer (Streamlit) — FIXED
# - Removed unsupported Cone `value` property (Plotly)
# - Color modes adapted to what Cone supports:
#     • Default (by vector norm)
#     • By Direction (Z): split into two traces (W≥0 vs W<0) with diverging scales
#     • By Magnitude: same as Default (explicit cmin/cmax)
# -------------------------------------------------------

import numpy as np
import streamlit as st
import plotly.graph_objects as go

# ================== PRESETS ==================
coil_configs = [
    (40, 11, -9), (34, 11, 7), (30, 11, 3), (32, 13, 9),
    (28, 11, 7), (28, 11, -9), (34, 15, -13), (80, 33, -27),
]
preset_labels = [f"N={c[0]}, +{c[1]}, {c[2]}" for c in coil_configs]

# ================== CORE GEOMETRY ==================
def generate_alternating_skip_sequence(corners: int, step_even: int, step_odd: int,
                                       radius: float = 1.0,
                                       z_layer: float = 0.0,
                                       angle_offset: float = 0.0):
    """Return vertex visitation sequence and 3D positions on a unit polygon ring."""
    sequence = []
    current = 1
    toggle = True
    for _ in range(corners + 1):  # close the loop
        sequence.append(current)
        step = step_even if toggle else step_odd
        current = (current + step - 1) % corners + 1
        toggle = not toggle

    # place polygon corners on unit circle, -pi/2 aligns first at +Y
    angles = np.linspace(0, 2*np.pi, corners, endpoint=False) - np.pi/2
    positions = [
        (radius*np.cos(angles[i % corners] + angle_offset),
         radius*np.sin(angles[i % corners] + angle_offset),
         z_layer)
        for i in sequence
    ]
    return {"sequence": sequence, "positions": positions}

def get_wire_arrows(all_positions):
    """Return oriented wire segments as (origin, vector). Flip Z-negative vectors to point upward for consistency."""
    arrows = []
    for i in range(len(all_positions) - 1):
        p0 = np.array(all_positions[i], dtype=float)
        p1 = np.array(all_positions[i + 1], dtype=float)
        v = p1 - p0
        if v[2] < 0:  # orient upward
            v = -v
            p0, p1 = p1, p0
        arrows.append((tuple(p0), tuple(v)))
    return arrows

# ================== FIELD (Biot–Savart-like direction) ==================
def compute_field_vectors(arrows,
                          grid_dims,
                          x_range,
                          y_range,
                          z_range):
    """
    Compute normalized direction field from a discrete set of wire segments using a Biot–Savart-like kernel.
    Returns grid (X,Y,Z), components (Bx,By,Bz) normalized, and magnitude |B| before normalization.
    """
    dl = 0.05  # small line element scaling along each segment
    x = np.linspace(*x_range, grid_dims[0])
    y = np.linspace(*y_range, grid_dims[1])
    z = np.linspace(*z_range, grid_dims[2])
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

    Bx = np.zeros_like(X, dtype=float)
    By = np.zeros_like(Y, dtype=float)
    Bz = np.zeros_like(Z, dtype=float)

    for origin, vector in arrows:
        x0, y0, z0 = origin
        dx, dy, dz = vector
        dl_vec = np.array([dx, dy, dz], dtype=float) * dl
        r0 = np.array([x0, y0, z0], dtype=float)

        RX = X - r0[0]
        RY = Y - r0[1]
        RZ = Z - r0[2]
        norm_R = np.sqrt(RX**2 + RY**2 + RZ**2) + 1e-8

        cross_x = dl_vec[1]*RZ - dl_vec[2]*RY
        cross_y = dl_vec[2]*RX - dl_vec[0]*RZ
        cross_z = dl_vec[0]*RY - dl_vec[1]*RX
        factor = 1.0 / (norm_R**3)

        Bx += cross_x * factor
        By += cross_y * factor
        Bz += cross_z * factor

    B_mag = np.sqrt(Bx**2 + By**2 + Bz**2) + 1e-12
    Bx_n = Bx / B_mag
    By_n = By / B_mag
    Bz_n = Bz / B_mag
    return X, Y, Z, Bx_n, By_n, Bz_n, B_mag

# ================== LINES (EVEN/ODD) ==================
def wire_segments_for_plot(seq, corners, z_layer, layer_spacing, filter_type):
    """Return polyline samples (x,y,z) grouped for plotly Scatter3d lines (even/odd edges)."""
    angles = np.linspace(0, 2*np.pi, corners, endpoint=False) - np.pi/2
    xs, ys, zs = [], [], []
    for i in range(len(seq) - 1):
        if (filter_type == "even" and (i % 2 == 1)) or (filter_type == "odd" and (i % 2 == 0)):
            continue

        a1 = angles[(seq[i] - 1) % corners]
        a2 = angles[(seq[i + 1] - 1) % corners]
        x1, y1 = np.cos(a1), np.sin(a1)
        x2, y2 = np.cos(a2), np.sin(a2)
        z1 = z_layer + layer_spacing * (i / (len(seq) - 1))
        z2 = z_layer + layer_spacing * ((i + 1) / (len(seq) - 1))

        xs.extend([x1, x2, None])
        ys.extend([y1, y2, None])
        zs.extend([z1, z2, None])
    return xs, ys, zs

# ================== STREAMLIT UI ==================
st.set_page_config(page_title="3-Phase Coil Visualizer", page_icon="🧲", layout="wide")

with st.sidebar:
    st.markdown("## Presets")
    preset = st.selectbox("Select preset", preset_labels, index=0)
    if st.button("Load preset", use_container_width=True):
        i = preset_labels.index(preset)
        c, f, b = coil_configs[i]
        st.session_state["corners"] = c
        st.session_state["skip_fwd"] = f
        st.session_state["skip_bwd"] = b

    st.markdown("---")
    st.markdown("## Geometry")
    corners = st.number_input("Corners (N)", min_value=3, step=1,
                              value=st.session_state.get("corners", coil_configs[0][0]))
    layers = st.number_input("Layers", min_value=1, step=1,
                             value=st.session_state.get("layers", 1))
    layer_spacing = st.number_input("Layer spacing", min_value=0.0, step=0.01, format="%.3f",
                                    value=st.session_state.get("layer_spacing", 0.15))

    col1, col2 = st.columns(2)
    with col1:
        skip_fwd = st.number_input("Skip forward (+)", step=1,
                                   value=st.session_state.get("skip_fwd", coil_configs[0][1]))
    with col2:
        skip_bwd = st.number_input("Skip backward (−)", step=1,
                                   value=st.session_state.get("skip_bwd", coil_configs[0][2]))

    st.markdown("---")
    st.markdown("## Field Grid")
    gx = st.slider("Grid XY resolution", 2, 60, 11)
    gz = st.slider("Grid Z resolution", 1, 40, 11)
    density = st.slider("Arrow density (subsample)", 1, 6, 2, help="Larger = fewer cones (faster).")

    st.markdown("Ranges")
    colx = st.columns(2)
    with colx[0]:
        x_min = st.number_input("x min", value=-2.0, step=0.1, format="%.2f")
        y_min = st.number_input("y min", value=-2.0, step=0.1, format="%.2f")
        z_min = st.number_input("z min", value=-1.0, step=0.1, format="%.2f")
    with colx[1]:
        x_max = st.number_input("x max", value= 2.0, step=0.1, format="%.2f")
        y_max = st.number_input("y max", value= 2.0, step=0.1, format="%.2f")
        z_max = st.number_input("z max", value= 1.0, step=0.1, format="%.2f")

    st.markdown("---")
    st.markdown("## Render")
    show_field = st.checkbox("Show field (cones)", value=True)
    show_even = st.checkbox("Show even segments", value=True)
    show_odd  = st.checkbox("Show odd segments", value=True)

    color_mode = st.radio(
        "Color mode",
        options=["Default (norm)", "By Direction (Z sign)", "By Magnitude"],
        index=0,
        help="Cone colors are limited to vector-norm-based scales; 'Z sign' is emulated via two traces."
    )

# cache for faster recompute across UI tweaks
@st.cache_data(show_spinner=False)
def _compute(corners, skip_fwd, skip_bwd, layers, layer_spacing,
             gx, gz, x_min, x_max, y_min, y_max, z_min, z_max):
    # 3-phase: offsets 0, 120°, 240°
    angles = [0.0, 2*np.pi/3, 4*np.pi/3]
    phases = []
    for a in angles:
        sd = generate_alternating_skip_sequence(corners, skip_fwd, skip_bwd, angle_offset=a)
        positions = []
        for L in range(layers):
            off = L * layer_spacing
            # replicate positions per layer with Z offset
            positions += [(x, y, z + off) for (x, y, z) in sd["positions"]]
        phases.append((sd["sequence"], positions))

    # Use phase-0 arrows for field (match original behavior)
    arrows = get_wire_arrows(phases[0][1])

    X, Y, Z, Bx, By, Bz, Bmag = compute_field_vectors(
        arrows,
        (gx, gx, gz),
        (x_min, x_max), (y_min, y_max), (z_min, z_max)
    )
    return phases, X, Y, Z, Bx, By, Bz, Bmag

# Compute
with st.spinner("Computing geometry and field…"):
    phases, X, Y, Z, Bx, By, Bz, Bmag = _compute(
        corners, skip_fwd, skip_bwd, layers, layer_spacing,
        gx, gz, x_min, x_max, y_min, y_max, z_min, z_max
    )

# Prepare figure
fig = go.Figure()

# Field cones
if show_field:
    # subsample for performance
    Xf = X[::density, ::density, ::density].flatten()
    Yf = Y[::density, ::density, ::density].flatten()
    Zf = Z[::density, ::density, ::density].flatten()
    U  = Bx[::density, ::density, ::density].flatten()
    V  = By[::density, ::density, ::density].flatten()
    W  = Bz[::density, ::density, ::density].flatten()
    M  = Bmag[::density, ::density, ::density].flatten()

    # Default and Magnitude use one trace colored by norm
    if color_mode in ("Default (norm)", "By Magnitude"):
        cmin = float(M.min())
        cmax = float(M.max())
        fig.add_trace(go.Cone(
            x=Xf, y=Yf, z=Zf,
            u=U, v=V, w=W,
            colorscale="Viridis" if color_mode == "By Magnitude" else "Teal",
            cmin=cmin, cmax=cmax,
            showscale=False,
            sizemode="absolute",
            sizeref=0.4 / (np.sqrt(max(1, len(Xf))) / 10 + 1e-6),
            anchor="tail",
            name="Field"
        ))
    else:
        # Emulate Z-sign coloring with two traces
        pos = W >= 0
        neg = ~pos
        # Positive W
        fig.add_trace(go.Cone(
            x=Xf[pos], y=Yf[pos], z=Zf[pos],
            u=U[pos], v=V[pos], w=W[pos],
            colorscale="Blues",
            showscale=False,
            sizemode="absolute",
            sizeref=0.4 / (np.sqrt(max(1, pos.sum())) / 10 + 1e-6),
            anchor="tail",
            name="W ≥ 0"
        ))
        # Negative W
        fig.add_trace(go.Cone(
            x=Xf[neg], y=Yf[neg], z=Zf[neg],
            u=U[neg], v=V[neg], w=W[neg],
            colorscale="Reds",
            showscale=False,
            sizemode="absolute",
            sizeref=0.4 / (np.sqrt(max(1, neg.sum())) / 10 + 1e-6),
            anchor="tail",
            name="W < 0"
        ))

# Wire segments (even/odd)
wire_colors = {"even": "#aa6600", "odd": "#880000"}
for (seq, _positions) in phases:
    for layer in range(layers):
        z_layer = layer * layer_spacing
        if show_even:
            xs, ys, zs = wire_segments_for_plot(seq, corners, z_layer, layer_spacing, "even")
            fig.add_trace(go.Scatter3d(
                x=xs, y=ys, z=zs, mode="lines",
                line=dict(width=5, color=wire_colors["even"]),
                name="Even segments",
                showlegend=False
            ))
        if show_odd:
            xs, ys, zs = wire_segments_for_plot(seq, corners, z_layer, layer_spacing, "odd")
            fig.add_trace(go.Scatter3d(
                x=xs, y=ys, z=zs, mode="lines",
                line=dict(width=5, color=wire_colors["odd"]),
                name="Odd segments",
                showlegend=False
            ))

# Layout
fig.update_layout(
    margin=dict(l=10, r=10, t=30, b=10),
    title=f"3-Phase Coil: N={corners}  Skip=({skip_fwd}, {skip_bwd})",
    scene=dict(
        xaxis=dict(title="x", showgrid=False, zeroline=False, showbackground=False),
        yaxis=dict(title="y", showgrid=False, zeroline=False, showbackground=False),
        zaxis=dict(title="z", showgrid=False, zeroline=False, showbackground=False),
        aspectmode="cube"
    ),
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("Notes & Limitations"):
    st.markdown(
        "- Plotly `Cone` colors are tied to vector **norm**; arbitrary per-point scalar coloring is not supported.\n"
        "- 'By Direction (Z sign)' is emulated by **two traces** (Blues for W≥0, Reds for W<0).\n"
        "- For true custom scalar coloring (e.g., by height layer), we can switch to **`Mesh3d` + glyphs** or WebGL quiver."
    )