import math
from dataclasses import dataclass

import numpy as np
import plotly.graph_objects as go
import streamlit as st

PRESETS = [
    (40, 11, -9),
    (34, 11, 7),
    (30, 11, 3),
    (32, 13, 9),
    (28, 11, 7),
    (28, 11, -9),
    (34, 15, -13),
    (80, 33, -27),
]

PRESET_LABELS = [f"N={c[0]}, +{c[1]}, {c[2]}" for c in PRESETS]


@dataclass
class CoilParams:
    coil_corners: int = PRESETS[0][0]
    skip_forward: int = PRESETS[0][1]
    skip_backward: int = PRESETS[0][2]
    num_layers: int = 1
    layer_spacing: float = 0.15
    grid_n: int = 9
    grid_z: int = 9
    extent_xy: float = 2.0
    extent_z: float = 1.0


def generate_sequence(corners: int, step_even: int, step_odd: int, radius: float = 1.0, z_layer: float = 0.0,
                      angle_offset: float = 0.0):
    sequence = []
    current = 1
    toggle = True
    for _ in range(corners + 1):
        sequence.append(current)
        step = step_even if toggle else step_odd
        current = (current + step - 1) % corners + 1
        toggle = not toggle
    angles = np.linspace(0, 2 * np.pi, corners, endpoint=False) - np.pi / 2
    positions = [
        (radius * np.cos(angles[(i - 1) % corners] + angle_offset),
         radius * np.sin(angles[(i - 1) % corners] + angle_offset),
         z_layer)
        for i in sequence
    ]
    return sequence, positions


def get_arrows(positions):
    arrows = []
    for i in range(len(positions) - 1):
        p0 = np.array(positions[i])
        p1 = np.array(positions[i + 1])
        v = p1 - p0
        if v[2] < 0:
            v = -v
        arrows.append((p0, v))
    return arrows


def compute_field_vectors(arrows, grid_n, grid_z, extent_xy, extent_z):
    dl = 0.05
    x = np.linspace(-extent_xy, extent_xy, grid_n)
    y = np.linspace(-extent_xy, extent_xy, grid_n)
    z = np.linspace(-extent_z, extent_z, grid_z)
    X, Y, Z = np.meshgrid(x, y, z, indexing='xy')
    Bx = np.zeros_like(X, dtype=float)
    By = np.zeros_like(Y, dtype=float)
    Bz = np.zeros_like(Z, dtype=float)
    for origin, vec in arrows:
        dl_vec = vec * dl
        r0 = origin
        RX = X - r0[0]
        RY = Y - r0[1]
        RZ = Z - r0[2]
        norm_R = np.sqrt(RX ** 2 + RY ** 2 + RZ ** 2) + 1e-8
        cross_x = dl_vec[1] * RZ - dl_vec[2] * RY
        cross_y = dl_vec[2] * RX - dl_vec[0] * RZ
        cross_z = dl_vec[0] * RY - dl_vec[1] * RX
        factor = 1 / (norm_R ** 3)
        Bx += cross_x * factor
        By += cross_y * factor
        Bz += cross_z * factor
    mag = np.sqrt(Bx ** 2 + By ** 2 + Bz ** 2) + 1e-9
    return X, Y, Z, Bx / mag, By / mag, Bz / mag, mag


def _layer_polyline(sequence, corners, layer_idx, params):
    angles = np.linspace(0, 2 * np.pi, corners, endpoint=False) - np.pi / 2
    lines = []
    for i in range(len(sequence) - 1):
        a1 = angles[(sequence[i] - 1) % corners]
        a2 = angles[(sequence[i + 1] - 1) % corners]
        x1, y1 = math.cos(a1), math.sin(a1)
        x2, y2 = math.cos(a2), math.sin(a2)
        z1 = layer_idx * params.layer_spacing
        z2 = layer_idx * params.layer_spacing
        lines.append(((x1, y1, z1), (x2, y2, z2)))
    return lines


@st.cache_data(show_spinner=False)
def build_coil_data(params: CoilParams, angle_offsets):
    phases = []
    for a in angle_offsets:
        seq, pos_layer0 = generate_sequence(params.coil_corners, params.skip_forward, params.skip_backward,
                                            angle_offset=a)
        positions = []
        for L in range(params.num_layers):
            offset = L * params.layer_spacing
            positions.extend([(x, y, z + offset) for x, y, z in pos_layer0])
        phases.append((seq, positions))
    arrows = get_arrows(phases[0][1])
    X, Y, Z, Bx, By, Bz, mag = compute_field_vectors(
        arrows,
        params.grid_n,
        params.grid_z,
        params.extent_xy,
        params.extent_z,
    )
    return {"phases": phases, "X": X, "Y": Y, "Z": Z, "Bx": Bx, "By": By, "Bz": Bz, "mag": mag}


def _build_field_cones(data, max_vectors, color_mode):
    X, Y, Z = data["X"], data["Y"], data["Z"]
    Bx, By, Bz = data["Bx"], data["By"], data["Bz"]
    mag = data["mag"]
    Xf = X.flatten()
    Yf = Y.flatten()
    Zf = Z.flatten()
    Bxf = Bx.flatten()
    Byf = By.flatten()
    Bzf = Bz.flatten()
    magf = mag.flatten()
    total = Xf.shape[0]
    if total > max_vectors:
        idx = np.linspace(0, total - 1, max_vectors, dtype=int)
        Xf, Yf, Zf = Xf[idx], Yf[idx], Zf[idx]
        Bxf, Byf, Bzf, magf = Bxf[idx], Byf[idx], Bzf[idx], magf[idx]
    sizeref = 0.5
    showscale = color_mode != "Default"
    colorscale = "Plasma" if color_mode != "Default" else "Teal"
    return go.Cone(
        x=Xf, y=Yf, z=Zf,
        u=Bxf, v=Byf, w=Bzf,
        sizemode="absolute", sizeref=sizeref,
        colorscale=colorscale,
        showscale=showscale,
        anchor="tail",
        colorbar_title=color_mode if showscale else None,
        name="Field vectors",
    )


def _build_wire_traces(phases, params, show_even, show_odd):
    traces = []
    for phase_idx, (seq, _) in enumerate(phases):
        color = ["#00ccff", "#33ff66", "#ff3366"][phase_idx % 3]
        for layer in range(params.num_layers):
            lines = _layer_polyline(seq, params.coil_corners, layer, params)
            xs, ys, zs = [], [], []
            for i, ((x1, y1, z1), (x2, y2, z2)) in enumerate(lines):
                is_even = i % 2 == 0
                if is_even and not show_even:
                    continue
                if (not is_even) and not show_odd:
                    continue
                xs.extend([x1, x2, None])
                ys.extend([y1, y2, None])
                zs.extend([z1, z2, None])
            if xs:
                traces.append(go.Scatter3d(
                    x=xs, y=ys, z=zs,
                    mode="lines",
                    line=dict(color=color, width=4),
                    name=f"Phase {phase_idx + 1} layer {layer + 1}",
                    opacity=0.85,
                ))
    return traces


def build_figure(params: CoilParams, show_field: bool, show_even: bool, show_odd: bool,
                 color_mode: str, max_vectors: int):
    angles = [0, 2 * np.pi / 3, 4 * np.pi / 3]
    data = build_coil_data(params, angles)
    fig = go.Figure()
    if show_field:
        fig.add_trace(_build_field_cones(data, max_vectors, color_mode))
    fig.add_traces(_build_wire_traces(data["phases"], params, show_even, show_odd))
    fig.update_layout(
        scene=dict(
            xaxis_title="X", yaxis_title="Y", zaxis_title="Z",
            aspectmode="cube",
            xaxis=dict(range=[-params.extent_xy, params.extent_xy]),
            yaxis=dict(range=[-params.extent_xy, params.extent_xy]),
            zaxis=dict(range=[-params.extent_z, params.extent_z]),
        ),
        legend=dict(orientation="h"),
        margin=dict(l=0, r=0, t=30, b=0),
        width=None,  # Use container width
        height=800,  # Fixed height to fill viewport
        autosize=True,
    )
    return fig


def st_app():
    try:
        st.set_page_config(page_title="Saw Shape Coil Field (Plotly 3D)", layout="wide")
    except Exception:
        pass
    st.title("🌀 Saw-Shape Coil Field — Plotly 3D Viewer")

    with st.sidebar:
        st.header("Preset & Geometry")
        preset = st.selectbox("Preset", PRESET_LABELS, index=0)
        preset_idx = PRESET_LABELS.index(preset)
        c, fwd, back = PRESETS[preset_idx]
        coil_corners = st.number_input("Corners", min_value=6, max_value=200, value=c, step=2)
        skip_forward = st.number_input("Skip forward", min_value=-200, max_value=200, value=fwd, step=1)
        skip_backward = st.number_input("Skip backward", min_value=-200, max_value=200, value=back, step=1)
        num_layers = st.slider("Layers", 1, 6, 1)
        layer_spacing = st.slider("Layer spacing", 0.05, 0.5, 0.15, step=0.01)

        st.markdown("---")
        st.header("Field Grid")
        grid_xy = st.slider("Grid XY resolution", 5, 23, 11, step=2)
        grid_z = st.slider("Grid Z resolution", 5, 21, 9, step=2)
        extent_xy = st.slider("XY extent", 1.0, 4.0, 2.0, step=0.1)
        extent_z = st.slider("Z extent", 0.5, 3.0, 1.0, step=0.1)

        st.markdown("---")
        st.header("Display")
        show_field = st.checkbox("Show field vectors", True)
        show_even = st.checkbox("Show even segments", True)
        show_odd = st.checkbox("Show odd segments", True)
        color_mode = st.selectbox("Field color mode", ["Default", "By Magnitude", "By Direction", "By Layer"])
        max_vectors = st.slider("Max field vectors", 100, 4000, 1200, step=100)

    params = CoilParams(
        coil_corners=int(coil_corners),
        skip_forward=int(skip_forward),
        skip_backward=int(skip_backward),
        num_layers=int(num_layers),
        layer_spacing=float(layer_spacing),
        grid_n=int(grid_xy),
        grid_z=int(grid_z),
        extent_xy=float(extent_xy),
        extent_z=float(extent_z),
    )

    fig = build_figure(params, show_field, show_even, show_odd, color_mode, max_vectors)
    st.plotly_chart(fig, width='stretch')
    st.caption("Tweak presets or parameters to explore linked saw-shaped coil geometries and their magnetic field direction.")


if __name__ == "__main__":
    st_app()