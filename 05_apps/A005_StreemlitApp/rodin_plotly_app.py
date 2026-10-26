# rodin_plotly_app.py
# Streamlit + Plotly 3D viewer for Rodin-Starship coil and dipole rings.
# Run: streamlit run rodin_plotly_app.py

import numpy as np
import streamlit as st
import plotly.graph_objects as go

# ----------------------------
# Geometry & Physics Helpers
# ----------------------------
def generate_rodin_starship(R=1.0, r=0.9, num_turns=10, num_points=2000):
    theta = np.linspace(0, num_turns * 2 * np.pi, num_points)
    phi = (2 + 2/5) * theta
    x = (R + r * np.cos(phi)) * np.cos(theta)
    y = (R + r * np.cos(phi)) * np.sin(theta)
    z = r * np.sin(phi)
    return x, y, z

def generate_dipole_ring(radius, num_magnets, z_offset=0.0, invert=False):
    positions, orientations = [], []
    for i in range(num_magnets):
        phi = 2 * np.pi * i / num_magnets
        x, y, z = radius * np.cos(phi), radius * np.sin(phi), z_offset
        mx = np.cos(2 * phi)
        my = np.sin(2 * phi)
        mz = np.cos(phi)
        m = np.array([mx, my, (-1 if invert else 1) * mz], dtype=float)
        m /= (np.linalg.norm(m) + 1e-12)
        positions.append(np.array([x, y, z], dtype=float))
        orientations.append(m)
    return positions, orientations

def _magnetic_field_dipoles_numpy(X, Y, Z, positions, orientations):
    """Vectorized dipole field superposition on grid (NumPy fallback)."""
    mu0 = 1.0
    R = np.stack([X, Y, Z], axis=-1)                     # [Nx,Ny,Nz,3]
    P = np.asarray(positions, dtype=float)               # [M,3]
    M = np.asarray(orientations, dtype=float)            # [M,3]

    Rm = R[..., None, :] - P.reshape((1,1,1,-1,3))       # [Nx,Ny,Nz,M,3]
    norm = np.linalg.norm(Rm, axis=-1)                   # [Nx,Ny,Nz,M]
    rhat = np.zeros_like(Rm)
    mask = norm > 1e-12
    rhat[mask] = Rm[mask] / norm[mask][..., None]

    inv3 = np.zeros_like(norm)
    inv3[mask] = 1.0 / (norm[mask] ** 3 + 1e-18)

    mdotr = np.einsum('...mj,mj->...m', rhat, M)         # [..., M]
    M_exp = M.reshape((1,1,1,-1,3))
    term = 3.0 * mdotr[..., None] * rhat - M_exp         # [Nx,Ny,Nz,M,3]

    B = (mu0 / (4.0 * np.pi)) * np.sum(term * inv3[..., None], axis=-2)
    return B[...,0], B[...,1], B[...,2]

def _biot_savart_wire_numpy(X, Y, Z, wire_points, current=1.0):
    """Biot–Savart field of a polyline current (NumPy fallback)."""
    mu0 = 1.0
    dl = np.diff(wire_points, axis=0)                     # [S,3]
    r_mid = 0.5 * (wire_points[:-1] + wire_points[1:])    # [S,3]
    R = np.stack([X, Y, Z], axis=-1)                      # [Nx,Ny,Nz,3]

    dBx = np.zeros_like(X, dtype=float)
    dBy = np.zeros_like(Y, dtype=float)
    dBz = np.zeros_like(Z, dtype=float)

    factor = (mu0 * current) / (4.0 * np.pi)
    for s in range(dl.shape[0]):
        Rseg = R - r_mid[s]                               # [Nx,Ny,Nz,3]
        norm = np.linalg.norm(Rseg, axis=-1)
        mask = norm > 1e-10

        cx = dl[s,1]*Rseg[...,2] - dl[s,2]*Rseg[...,1]
        cy = dl[s,2]*Rseg[...,0] - dl[s,0]*Rseg[...,2]
        cz = dl[s,0]*Rseg[...,1] - dl[s,1]*Rseg[...,0]

        inv = np.zeros_like(norm)
        inv[mask] = 1.0 / (norm[mask]**3 + 1e-18)

        dBx += factor * cx * inv
        dBy += factor * cy * inv
        dBz += factor * cz * inv
    return dBx, dBy, dBz

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Rodin + Dipole Rings (Plotly 3D)", layout="wide")
def st_app():
    # In embedded mode, set_page_config may already have been called; ignore if so.
    try:
        st.set_page_config(page_title="Rodin + Dipole Rings (Plotly 3D)", layout="wide")
    except Exception:
        pass
    st.title("🧲 Rodin-Starship Coil & Dipole Rings — Plotly 3D Viewer")

    with st.sidebar:
        st.header("Parameters")
        num_magnets = st.slider("Number of magnets per ring", 4, 64, 16, step=1)
        ring_radius = st.slider("Dipole ring radius", 0.1, 2.0, 0.5, step=0.05)
        rodin_major = st.slider("Rodin major R", 0.3, 2.5, 1.0, step=0.05)
        rodin_minor = st.slider("Rodin minor r", 0.1, 2.0, 0.9, step=0.05)
        num_turns = st.slider("Rodin turns", 1, 30, 10, step=1)

        st.markdown("---")
        st.header("Field Grid")
        grid_N = st.slider("Grid resolution (N×N×N)", 5, 17, 9, step=2)
        world_extent = st.slider("Extent (±X=±Y=±Z)", 1.0, 4.0, 2.0, step=0.5)

        st.markdown("---")
        st.header("Components")
        show_bottom_field = st.checkbox("Include bottom ring field", True)
        show_top_field = st.checkbox("Include top ring field", True)
        show_rodin_field = st.checkbox("Include Rodin wire field", True)
        show_bottom_geom = st.checkbox("Show bottom ring geometry", True)
        show_top_geom = st.checkbox("Show top ring geometry", True)
        show_rodin_geom = st.checkbox("Show Rodin geometry", True)

        st.markdown("---")
        st.header("Cones / Vectors")
        max_cones = st.slider("Max cones displayed", 100, 3000, 800, step=100)
        cone_sizeref = st.slider("Cone size (sizeref)", 0.1, 3.0, 0.8, step=0.1)
        norm_vectors = st.checkbox("Normalize vectors", True)

    # Geometry
    bottom_pos, bottom_ori = generate_dipole_ring(ring_radius, num_magnets, z_offset=-0.75, invert=False)
    top_pos, top_ori = generate_dipole_ring(ring_radius, num_magnets, z_offset=0.75, invert=True)
    rx, ry, rz = generate_rodin_starship(R=rodin_major, r=rodin_minor, num_turns=num_turns, num_points=2000)
    rodin_wire_points = np.stack([rx, ry, rz], axis=-1)

    # Grid
    axis = np.linspace(-world_extent, world_extent, grid_N)
    X, Y, Z = np.meshgrid(axis, axis, axis, indexing="xy")

    # Fields
    Bx = np.zeros_like(X, dtype=float)
    By = np.zeros_like(Y, dtype=float)
    Bz = np.zeros_like(Z, dtype=float)

    if show_bottom_field:
        bx, by, bz = _magnetic_field_dipoles_numpy(X, Y, Z, bottom_pos, bottom_ori)
        Bx += bx; By += by; Bz += bz

    if show_top_field:
        bx, by, bz = _magnetic_field_dipoles_numpy(X, Y, Z, top_pos, top_ori)
        Bx += bx; By += by; Bz += bz

    if show_rodin_field:
        bx, by, bz = _biot_savart_wire_numpy(X, Y, Z, rodin_wire_points, current=1.0)
        Bx += bx; By += by; Bz += bz

    # Normalize (optional) for visualization
    mag = np.sqrt(Bx**2 + By**2 + Bz**2) + 1e-18
    if norm_vectors:
        U = Bx / mag
        V = By / mag
        W = Bz / mag
    else:
        U, V, W = Bx, By, Bz

    # Downsample cones to keep performance reasonable
    coords = np.stack([X.ravel(), Y.ravel(), Z.ravel(), U.ravel(), V.ravel(), W.ravel()], axis=1)
    # Remove near-zero vectors to declutter
    vec_norms = np.linalg.norm(coords[:,3:], axis=1)
    thr = 1e-6 if norm_vectors else np.percentile(vec_norms, 5)
    mask_nonzero = vec_norms > thr
    coords = coords[mask_nonzero]
    if coords.shape[0] > max_cones:
        step = int(np.ceil(coords.shape[0] / max_cones))
        coords = coords[::step]

    # ----------------------------
    # Build Plotly Figure
    # ----------------------------
    fig = go.Figure()

    # Field cones
    if coords.size > 0:
        fig.add_trace(go.Cone(
            x=coords[:,0], y=coords[:,1], z=coords[:,2],
            u=coords[:,3], v=coords[:,4], w=coords[:,5],
            sizemode="absolute", sizeref=cone_sizeref,
            showscale=False, anchor="tail", name="Field"
        ))

    # Rodin geometry
    if show_rodin_geom:
        fig.add_trace(go.Scatter3d(
            x=rx, y=ry, z=rz, mode="lines",
            line=dict(width=4), name="Rodin coil"
        ))

    # Dipole ring geometry as cones for orientation
    def add_ring_cones(positions, orientations, name):
        P = np.asarray(positions); M = np.asarray(orientations)
        if P.shape[0] == 0: return
        fig.add_trace(go.Cone(
            x=P[:,0], y=P[:,1], z=P[:,2],
            u=M[:,0], v=M[:,1], w=M[:,2],
            sizemode="absolute", sizeref=0.4, anchor="tail",
            showscale=False, name=name, opacity=0.8
        ))

    if show_bottom_geom:
        add_ring_cones(bottom_pos, bottom_ori, "Bottom ring dipoles")
    if show_top_geom:
        add_ring_cones(top_pos, top_ori, "Top ring dipoles")

    fig.update_layout(
        scene=dict(
            xaxis_title="X", yaxis_title="Y", zaxis_title="Z",
            aspectmode="cube",
            xaxis=dict(range=[-world_extent, world_extent]),
            yaxis=dict(range=[-world_extent, world_extent]),
            zaxis=dict(range=[-world_extent, world_extent]),
        ),
        legend=dict(orientation="h"),
        margin=dict(l=0, r=0, t=30, b=0),
        width=None,  # Use container width
        height=800,  # Fixed height to fill viewport
        autosize=True,
    )

    st.plotly_chart(fig, width='stretch')

    st.caption("Tip: Reduce grid resolution or max cones if rendering is slow. Use normalization to visualize direction only.")

if __name__ == "__main__":
    st_app()