# views/magnet_ring_view.py
from __future__ import annotations

import os
import sys

import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# ---------------------------------------------------------
# Zorg dat de project-root op sys.path staat (1 niveau boven /views)
# ---------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ---------------------------------------------------------
# Nu kunnen we coil_geometries altijd vinden zoals in app.py
# ---------------------------------------------------------
from coil_geometries.magnet_ring import generate_magnet_dipole_ring

# LET OP: pas deze regel aan naar jouw echte module/klasse:
# - als Rodin3PhaseSingle in coil_geometries/__init__.py wordt geëxporteerd:
from coil_geometries import Rodin3PhaseSingle
# of, als hij in bijvoorbeeld coil_geometries/rodin_3phase.py staat:
# from coil_geometries.rodin_3phase import Rodin3PhaseSingle

from .field_utils import (
    field_from_segments,
    field_from_dipoles,
    build_segments_from_polylines,
    make_xy_plane_grid,
)


def render_magnet_ring_view() -> None:
    st.title("Magnetenring + Coil – Mixed EM / Swirl Field")

    st.markdown(
        """
Deze view doet twee dingen:

1. Visualiseert een ring van kantelende magneten (dipolen) met sliders.
2. Berekent het gecombineerde veld van:
   - een gekozen coil-geometrie (nu: Rodin 3-Phase Single), en  
   - de magnetenring  
   op **hetzelfde Biot–Savart grid** (XY-vlak), en plot de veldsterkte.
"""
    )

    # -------------------------
    # Sidebar: magnet-ring parameters
    # -------------------------
    st.sidebar.header("Magnetenring")

    num_magnets = st.sidebar.slider("Aantal magneten", 2, 64, 16, 1)
    ring_radius = st.sidebar.slider("Ringradius [m]", 0.05, 0.5, 0.20, 0.01)
    toroidal_deg = st.sidebar.slider("Toroidale twist [°]", 0, 1440, 720, 45)
    poloidal_deg = st.sidebar.slider("Poloidale tilt amplitude [°]", 0, 720, 90, 15)

    dipole_strength = st.sidebar.slider(
        "Relatieve dipoolsterkte", 0.1, 5.0, 1.0, 0.1
    )

    # -------------------------
    # Sidebar: coil parameters (Rodin 3-phase single)
    # -------------------------
    st.sidebar.header("Rodin Coil (3-Phase Single)")

    coil_model = Rodin3PhaseSingle()

    R_major = st.sidebar.slider(
        "Hoofd-radius R [m]", 0.02, 0.20, 0.07, 0.005
    )
    r_ratio = st.sidebar.slider(
        "Minor-radius verhouding r/R", 0.1, 0.9, 0.618, 0.01
    )
    p = st.sidebar.slider("p (torus-knoop)", 1, 20, 5, 1)
    q = st.sidebar.slider("q (torus-knoop)", 1, 40, 12, 1)

    coil_current = st.sidebar.slider(
        "Coilstroom I [A]", 0.0, 50.0, 10.0, 1.0
    )

    # -------------------------
    # Sidebar: veld-grid en plot
    # -------------------------
    st.sidebar.header("Field Grid / Plot")

    grid_span = st.sidebar.slider("XY-span [m]", 0.1, 0.6, 0.3, 0.05)
    grid_n = st.sidebar.slider("Grid resolutie", 15, 80, 35, 5)
    z_plane = st.sidebar.slider("Z-vlak [m]", -0.2, 0.2, 0.0, 0.01)

    show_components = st.sidebar.multiselect(
        "Veldcomponenten in mixed field:",
        ["Coil alleen", "Magneten alleen", "Coil + Magneten"],
        default=["Coil + Magneten"],
    )

    # --------------------------------------------------
    # 1. Magnetenring: posities + dipoolmomenten
    # --------------------------------------------------
    positions, moments = generate_magnet_dipole_ring(
        num_magnets=num_magnets,
        radius=ring_radius,
        toroidal_degrees=toroidal_deg,
        poloidal_degrees=poloidal_deg,
    )
    # schaal dipoolmomenten
    moments_scaled = moments * dipole_strength

    # 3D visualisatie van ring + coil-geometrie
    fig3d = go.Figure()

    # Magneten als pijlen (cones)
    fig3d.add_trace(
        go.Cone(
            x=positions[:, 0],
            y=positions[:, 1],
            z=positions[:, 2],
            u=moments_scaled[:, 0],
            v=moments_scaled[:, 1],
            w=moments_scaled[:, 2],
            sizemode="absolute",
            sizeref=0.1 * dipole_strength,
            showscale=False,
            colorscale="HSV",
            name="Magneten",
            anchor="tip",
        )
    )

    # --------------------------------------------------
    # 2. Coil-polylines uit Rodin-model
    # --------------------------------------------------
    coil_params = {
        "R_major_m": float(R_major),
        "r_ratio": float(r_ratio),
        "p": float(p),
        "q": float(q),
    }
    polylines = coil_model.build_polylines(coil_params, points_per_turn=800)
    segments = build_segments_from_polylines(polylines)

    # coil tekenen
    for poly in polylines:
        fig3d.add_trace(
            go.Scatter3d(
                x=poly[:, 0],
                y=poly[:, 1],
                z=poly[:, 2],
                mode="lines",
                line=dict(width=4, color="orange"),
                name="Rodin Coil",
                showlegend=False,
            )
        )

    fig3d.update_layout(
        scene=dict(
            xaxis_title="X [m]",
            yaxis_title="Y [m]",
            zaxis_title="Z [m]",
            aspectmode="data",
        ),
        title="Magnetenring + Rodin 3-Phase Coil (geometrie)",
    )

    st.plotly_chart(fig3d, use_container_width=True)

    # --------------------------------------------------
    # 3. Mixed field op één XY-plane grid
    # --------------------------------------------------
    st.subheader("Mixed Field op XY-vlak")

    pts, Xg, Yg, Zg = make_xy_plane_grid(
        x_min=-grid_span,
        x_max=+grid_span,
        y_min=-grid_span,
        y_max=+grid_span,
        z_plane=z_plane,
        n_x=grid_n,
        n_y=grid_n,
    )

    B_coil = field_from_segments(pts, segments, current=coil_current)
    B_dip = field_from_dipoles(pts, positions, moments_scaled)

    # Verschillende combinaties
    B_abs_coil = np.linalg.norm(B_coil, axis=1).reshape(Xg.shape)
    B_abs_dip = np.linalg.norm(B_dip, axis=1).reshape(Xg.shape)
    B_abs_mix = np.linalg.norm(B_coil + B_dip, axis=1).reshape(Xg.shape)

    fig_field = go.Figure()

    if "Coil alleen" in show_components:
        fig_field.add_trace(
            go.Heatmap(
                x=np.linspace(-grid_span, grid_span, grid_n),
                y=np.linspace(-grid_span, grid_span, grid_n),
                z=B_abs_coil,
                colorscale="Viridis",
                colorbar=dict(title="|B| coil [T]"),
                zsmooth="best",
                name="Coil alleen",
                opacity=0.7,
            )
        )

    if "Magneten alleen" in show_components:
        fig_field.add_trace(
            go.Heatmap(
                x=np.linspace(-grid_span, grid_span, grid_n),
                y=np.linspace(-grid_span, grid_span, grid_n),
                z=B_abs_dip,
                colorscale="Plasma",
                colorbar=dict(title="|B| magneten [T]"),
                zsmooth="best",
                name="Magneten alleen",
                opacity=0.6,
                showscale=False,
            )
        )

    if "Coil + Magneten" in show_components:
        fig_field.add_trace(
            go.Heatmap(
                x=np.linspace(-grid_span, grid_span, grid_n),
                y=np.linspace(-grid_span, grid_span, grid_n),
                z=B_abs_mix,
                colorscale="Inferno",
                colorbar=dict(title="|B| totaal [T]"),
                zsmooth="best",
                name="Coil + Magneten",
                opacity=0.75,
                showscale=True,
            )
        )

    fig_field.update_layout(
        xaxis_title="X [m]",
        yaxis_title="Y [m]",
        title=f"Veldsterkte |B| op z = {z_plane:.3f} m",
        yaxis=dict(scaleanchor="x", scaleratio=1),
    )

    st.plotly_chart(fig_field, use_container_width=True)

    st.markdown(
        r"""
**Interpretatie:**

- Heldere zones in de mixed map (**Coil + Magneten**) zijn plekken waar beide velden samen sterk zijn.  
- Donkere/uitgedoofde zones zijn kandidaten voor “swirl pressure wells” of juist nulpunten, afhankelijk van je SST metric.  
- Omdat zowel coil als ring dezelfde punten gebruiken, kun je later hier meteen
  jouw \(1-G\) of \(\|\mathbf g\|\)-metrics bovenop loslaten (zelfde grid, zelfde B).
"""
    )