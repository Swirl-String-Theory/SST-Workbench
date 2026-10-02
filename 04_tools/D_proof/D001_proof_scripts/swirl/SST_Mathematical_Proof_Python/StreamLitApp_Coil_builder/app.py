
# app.py
"""
Coil Analyzer – Streamlit + Plotly
----------------------------------
- Extensible coil model registry
- Skin-effect in copper
- Approx. AC resistance
- Rough inductance/Q estimate
- Biot–Savart with multi-phase Rodin coils (3-phase & double 3-phase)

Voeg nieuwe spoeltypes toe door een nieuwe CoilModel-subclass te maken
en hem te registreren in COIL_REGISTRY.
"""

from __future__ import annotations

from dataclasses import dataclass, field

field()
from typing import Dict, List
from views import render_magnet_ring_view

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from coil_geometries import (
    CoilModel,
    CoilParameter,
    MU_0,
    Rodin3PhaseSingle,
    Rodin3PhaseDouble,
    DomeTrapCoil,
    SawBowlCoil,
)
from sst_swirl_gravity import (
    compute_vorticity,
    compute_swirl_curvature_tensor,
    compute_swirl_gravity,
)

# ==========================================
# 0. Fysische constanten
# ==========================================

MU_0 = 4.0 * np.pi * 1e-7     # H/m, vacuum permeability
SIGMA_CU = 5.8e7              # S/m, copper conductivity
RHO_CU = 1.68e-8              # Ohm*m, copper resistivity


# ==========================================
# 1. Skin-effect & AC-weerstand
# ==========================================

def skin_depth_copper(f_hz: np.ndarray) -> np.ndarray:
    """
    Skin depth δ(f) for copper in meter.
    f_hz may be scalar or array.
    """
    f = np.asarray(f_hz, dtype=float)
    omega = 2.0 * np.pi * f
    delta = np.sqrt(2.0 / (omega * MU_0 * SIGMA_CU))
    return delta


def ac_resistance_round_wire(
        f_hz: float,
        rho: float,
        length_m: float,
        radius_m: float,
) -> float:
    """
    Eenvoudig AC-weerstandsmodel voor ronde geleider.

    - Voor lage f (δ >> R): DC weerstand.
    - Voor hoge f (δ << R): R_ac ~ R_dc * (R / (2 δ))

    Dit is een eerste-orde model. Proximity-effect etc. kun je later toevoegen.
    """
    if f_hz <= 0:
        # DC
        area = np.pi * radius_m**2
        return rho * length_m / area

    delta = skin_depth_copper(f_hz)
    area = np.pi * radius_m**2
    R_dc = rho * length_m / area

    if delta > 3 * radius_m:
        # bijna uniform; DC-dominant
        return float(R_dc)
    elif delta < 0.1 * radius_m:
        # sterke skin; eenvoudige schaal
        return float(R_dc * (radius_m / (2.0 * delta)))
    else:
        # lineaire interpolatie tussen DC en high-f model
        R_high = R_dc * (radius_m / (2.0 * delta))
        w = (3 * radius_m - delta) / (3 * radius_m - 0.1 * radius_m)
        w = np.clip(w, 0.0, 1.0)
        return float((1 - w) * R_dc + w * R_high)


# ==========================================
# 2. Biot–Savart (vectorized, per coil polyline)
# ==========================================

def compute_field_vectorized(points: np.ndarray,
                             coil_polyline: np.ndarray,
                             I: float) -> np.ndarray:
    """
    Vectorized Biot-Savart Law voor één spoel-polyline.

    Parameters
    ----------
    points : (M, 3) array
        Evaluatiepunten.
    coil_polyline : (N, 3) array
        Geometrische punten langs de spoel (in volgorde).
    I : float
        Stroom [A] door de spoel (zelfde richting als polyline).

    Returns
    -------
    B : (M, 3) array
        B-veld [T] op alle punten.
    """
    # Segmenten
    dl = np.diff(coil_polyline, axis=0)                      # (N-1, 3)
    mid = (coil_polyline[:-1] + coil_polyline[1:]) / 2.0     # (N-1, 3)

    # r_vec: (M, N-1, 3)
    r_vec = points[:, np.newaxis, :] - mid[np.newaxis, :, :]
    dist = np.linalg.norm(r_vec, axis=2)                     # (M, N-1)
    dist[dist < 1e-9] = 1e-9

    # Cross product dL x r_vec
    cross = np.cross(dl[np.newaxis, :, :], r_vec)            # (M, N-1, 3)

    # Biot–Savart factor
    factor = (MU_0 * I) / (4 * np.pi * dist**3)              # (M, N-1)
    factor = factor[..., np.newaxis]                         # (M, N-1, 1)

    B = np.sum(cross * factor, axis=1)                       # (M, 3)
    return B


# -----------------------
# SST Gravity metric (extra)
# -----------------------

class SSTGravityMetric:
    V_SWIRL_CANON = 1.09384563e6

    @staticmethod
    def compute_gravity_dilation(
            B_field: np.ndarray,
            omega_drive: float,
            v_swirl: float = V_SWIRL_CANON,
            B_saturation: float = 5.0,
    ) -> np.ndarray:
        """
        G_local = 1 - ( (B/B_sat) * log10(omega) )^2, clipped to [0,1].
        """
        B_mag = np.linalg.norm(B_field, axis=1)
        freq_scale = np.log10(omega_drive) if omega_drive > 1.0 else 0.0
        coupling = (B_mag / B_saturation) * freq_scale
        G = 1.0 - np.square(coupling)
        return np.clip(G, 0.0, 1.0)


# -----------------------
# Coil registry
# -----------------------

COIL_REGISTRY: Dict[str, CoilModel] = {
    "rodin_single": Rodin3PhaseSingle(),
    "rodin_double": Rodin3PhaseDouble(),
    "dome_trap": DomeTrapCoil(),
    "saw_bowl": SawBowlCoil(),
}


# ==========================================
# 3. Coil-model basis
# ==========================================

@dataclass
class CoilParameter:
    name: str
    label: str
    default: float
    min_value: float
    max_value: float
    step: float
    is_int: bool = False


@dataclass
class CoilModel:
    """
    Abstracte basis voor spoelgeometrieën.

    Subclasses implementeren:
      - build_polylines(params, points_per_turn) -> List[np.ndarray] (elk (N,3))
      - estimate_inductance(params, polylines) -> float
    """
    name: str = "base"
    parameters: Dict[str, CoilParameter] = field(default_factory=dict)

    # ---- verplichte API ----
    def build_polylines(
            self,
            params: Dict[str, float],
            points_per_turn: int = 200,
    ) -> List[np.ndarray]:
        raise NotImplementedError

    def estimate_inductance(
            self,
            params: Dict[str, float],
            polylines: List[np.ndarray],
    ) -> float:
        raise NotImplementedError

    # ---- standaard helper-functies ----
    def build_segments(self,
                       params: Dict[str, float],
                       points_per_turn: int = 200) -> np.ndarray:
        """
        Converteer polylines naar (M, 2, 3) segmenten.
        """
        polylines = self.build_polylines(params, points_per_turn)
        segs = []
        for poly in polylines:
            seg = np.stack([poly[:-1], poly[1:]], axis=1)  # (N-1, 2, 3)
            segs.append(seg)
        return np.concatenate(segs, axis=0)

    def wire_length(self, params: Dict[str, float],
                    points_per_turn: int = 200) -> float:
        """
        Totale draadlengte uit polylines.
        """
        polylines = self.build_polylines(params, points_per_turn)
        total = 0.0
        for poly in polylines:
            dl = np.diff(poly, axis=0)
            total += np.linalg.norm(dl, axis=1).sum()
        return float(total)


# ==========================================
# 4. Eenvoudige referentie-spoelen
# ==========================================

@dataclass
class SimpleCircularCoil(CoilModel):
    """
    N-turn pancake coil (alle windingen in één vlak).
    """
    name: str = "Simple Circular Coil"
    parameters: Dict[str, CoilParameter] = field(default_factory=lambda: {
        "radius_m": CoilParameter(
            name="radius_m", label="Radius [m]",
            default=0.05, min_value=0.005, max_value=0.5, step=0.005
        ),
        "turns": CoilParameter(
            name="turns", label="Turns",
            default=10, min_value=1, max_value=200, step=1, is_int=True
        ),
    })

    def build_polylines(
            self,
            params: Dict[str, float],
            points_per_turn: int = 200,
    ) -> List[np.ndarray]:
        R = params["radius_m"]
        N_turns = int(params["turns"])

        polylines: List[np.ndarray] = []
        for n in range(N_turns):
            r_n = R * (0.5 + 0.5 * n / max(N_turns - 1, 1))
            theta = np.linspace(0.0, 2 * np.pi, points_per_turn + 1)
            x = r_n * np.cos(theta)
            y = r_n * np.sin(theta)
            z = np.zeros_like(x)
            poly = np.stack([x, y, z], axis=1)
            polylines.append(poly)

        return polylines

    def estimate_inductance(
            self,
            params: Dict[str, float],
            polylines: List[np.ndarray],
    ) -> float:
        # Wheeler-achtige benadering voor pancake coil
        R = params["radius_m"]
        N_turns = float(params["turns"])
        w = R
        L = MU_0 * N_turns**2 * R**2 / (8 * R + 11 * w)
        return float(L)


@dataclass
class SimpleSolenoidCoil(CoilModel):
    """
    Solenoidachtige spoel.
    """
    name: str = "Simple Solenoid"
    parameters: Dict[str, CoilParameter] = field(default_factory=lambda: {
        "radius_m": CoilParameter(
            name="radius_m", label="Radius [m]",
            default=0.03, min_value=0.005, max_value=0.5, step=0.005
        ),
        "length_m": CoilParameter(
            name="length_m", label="Lengte [m]",
            default=0.1, min_value=0.01, max_value=1.0, step=0.005
        ),
        "turns": CoilParameter(
            name="turns", label="Turns",
            default=50, min_value=1, max_value=1000, step=1, is_int=True
        ),
    })

    def build_polylines(
            self,
            params: Dict[str, float],
            points_per_turn: int = 200,
    ) -> List[np.ndarray]:
        R = params["radius_m"]
        L = params["length_m"]
        N_turns = int(params["turns"])

        total_points = N_turns * points_per_turn
        theta = np.linspace(0.0, 2 * np.pi * N_turns, total_points + 1)
        z = np.linspace(-L / 2, L / 2, total_points + 1)
        x = R * np.cos(theta)
        y = R * np.sin(theta)

        poly = np.stack([x, y, z], axis=1)
        return [poly]

    def estimate_inductance(
            self,
            params: Dict[str, float],
            polylines: List[np.ndarray],
    ) -> float:
        R = params["radius_m"]
        L_len = params["length_m"]
        N_turns = float(params["turns"])
        A = np.pi * R**2
        L = MU_0 * N_turns**2 * A / L_len
        return float(L)


# ==========================================
# 5. Rodin torus-knoop geometrie (jouw code)
# ==========================================

def generate_rodin_phase(
        R: float,
        r: float,
        p: int,
        q: int,
        phase_shift_angle: float,
        direction: int = 1,
        num_points: int = 2000,
) -> np.ndarray:
    """
    Eén Rodin/torus-knoop fase.

    direction = +1 (bijv. CCW), -1 (gespiegeld CW).
    """
    theta = np.linspace(0, 2 * np.pi * p, num_points)  # sluit na p periodes
    phi = (direction * (q / p) * theta) + phase_shift_angle

    x = (R + r * np.cos(phi)) * np.cos(theta)
    y = (R + r * np.cos(phi)) * np.sin(theta)
    z = r * np.sin(phi)
    return np.stack([x, y, z], axis=1)


@dataclass
class Rodin3PhaseSingle(CoilModel):
    """
    Enkele 3-phase Rodin coil (alle drie fasen zelfde chirality).
    Gebaseerd op generate_rodin_phase (p,q torus-knoop).
    """
    name: str = "Rodin 3-Phase (single chirality)"
    parameters: Dict[str, CoilParameter] = field(default_factory=lambda: {
        "R_major_m": CoilParameter(
            name="R_major_m", label="Hoofd-radius R [m]",
            default=0.07, min_value=0.01, max_value=0.3, step=0.005
        ),
        "r_ratio": CoilParameter(
            name="r_ratio", label="Minor-radius verhouding r/R",
            default=0.618, min_value=0.1, max_value=0.9, step=0.01
        ),
        "p": CoilParameter(
            name="p", label="p (torus-knoop index)",
            default=5, min_value=1, max_value=20, step=1, is_int=True
        ),
        "q": CoilParameter(
            name="q", label="q (torus-knoop index)",
            default=12, min_value=1, max_value=40, step=1, is_int=True
        ),
    })

    def build_polylines(
            self,
            params: Dict[str, float],
            points_per_turn: int = 2000,
    ) -> List[np.ndarray]:
        R = params["R_major_m"]
        r_ratio = params["r_ratio"]
        p = int(params["p"])
        q = int(params["q"])
        r = R * r_ratio

        # 3 fasen, 0°, 120°, 240°
        shifts = [0.0, 2 * np.pi / 3, 4 * np.pi / 3]
        polylines: List[np.ndarray] = []
        for shift in shifts:
            poly = generate_rodin_phase(
                R=R,
                r=r,
                p=p,
                q=q,
                phase_shift_angle=shift,
                direction=1,            # CCW (bijv.)
                num_points=points_per_turn,
            )
            polylines.append(poly)
        return polylines

    def estimate_inductance(
            self,
            params: Dict[str, float],
            polylines: List[np.ndarray],
    ) -> float:
        """
        Groffe orde: benader als solenoïde op een torus,
        met effectieve lengte ~ 2πR en N_eff ~ p*q/???.
        Voor nu: gebruik effectieve N uit p, q.
        """
        R = params["R_major_m"]
        r_ratio = params["r_ratio"]
        p = float(params["p"])
        q = float(params["q"])

        R_torus = R
        A = np.pi * (R * r_ratio)**2
        L_len = 2.0 * np.pi * R_torus
        # effectieve windingen: p*q is een typische torus-knoop "wrapping"
        N_eff = p * q
        L = MU_0 * N_eff**2 * A / L_len
        return float(L)


@dataclass
class Rodin3PhaseDouble(CoilModel):
    """
    Double 3-Phase Rodin CW & CCW:
    - 3 fasen met direction=+1
    - 3 fasen met direction=-1 (gespiegeld)
    ===> 6 polylines totaal
    """
    name: str = "Rodin 3-Phase (double CW & CCW)"
    parameters: Dict[str, CoilParameter] = field(default_factory=lambda: {
        "R_major_m": CoilParameter(
            name="R_major_m", label="Hoofd-radius R [m]",
            default=0.07, min_value=0.01, max_value=0.3, step=0.005
        ),
        "r_ratio": CoilParameter(
            name="r_ratio", label="Minor-radius verhouding r/R",
            default=0.618, min_value=0.1, max_value=0.9, step=0.01
        ),
        "p": CoilParameter(
            name="p", label="p (torus-knoop index)",
            default=5, min_value=1, max_value=20, step=1, is_int=True
        ),
        "q": CoilParameter(
            name="q", label="q (torus-knoop index)",
            default=12, min_value=1, max_value=40, step=1, is_int=True
        ),
    })

    def build_polylines(
            self,
            params: Dict[str, float],
            points_per_turn: int = 2000,
    ) -> List[np.ndarray]:
        R = params["R_major_m"]
        r_ratio = params["r_ratio"]
        p = int(params["p"])
        q = int(params["q"])
        r = R * r_ratio

        shifts = [0.0, 2 * np.pi / 3, 4 * np.pi / 3]
        polylines: List[np.ndarray] = []

        # CW (direction=+1)
        for shift in shifts:
            poly = generate_rodin_phase(
                R=R, r=r, p=p, q=q,
                phase_shift_angle=shift,
                direction=+1,
                num_points=points_per_turn,
            )
            polylines.append(poly)

        # CCW gespiegeld (direction=-1)
        for shift in shifts:
            poly = generate_rodin_phase(
                R=R, r=r, p=p, q=q,
                phase_shift_angle=shift,
                direction=-1,
                num_points=points_per_turn,
            )
            polylines.append(poly)

        return polylines

    def estimate_inductance(
            self,
            params: Dict[str, float],
            polylines: List[np.ndarray],
    ) -> float:
        """
        Heel ruwe schatting: zelfde formule als Rodin3PhaseSingle,
        maar met factor ~2 voor dubbele spoel.
        """
        R = params["R_major_m"]
        r_ratio = params["r_ratio"]
        p = float(params["p"])
        q = float(params["q"])

        R_torus = R
        A = np.pi * (R * r_ratio)**2
        L_len = 2.0 * np.pi * R_torus
        N_eff = p * q
        L_single = MU_0 * N_eff**2 * A / L_len
        return float(2.0 * L_single)


# ==========================================
# 6. Registry – makkelijk uitbreiden
# ==========================================

COIL_REGISTRY: Dict[str, CoilModel] = {
    "rodin_3phase_single": Rodin3PhaseSingle(),
    "rodin_3phase_double": Rodin3PhaseDouble(),
    "dome_trap": DomeTrapCoil(),
    "simple_circular": SimpleCircularCoil(),
    "simple_solenoid": SimpleSolenoidCoil(),
}


# -----------------------
# Streamlit UI
# -----------------------

def render_coil_analyzer():
    st.title("Coil Analyzer – Geometries, Skin, L, Q, |B| & SST Gravity Metric")

    # --- coil type ---
    coil_key = st.sidebar.selectbox(
        "Spoeltype",
        options=list(COIL_REGISTRY.keys()),
        format_func=lambda k: COIL_REGISTRY[k].name,
    )
    coil_model = COIL_REGISTRY[coil_key]

    st.sidebar.subheader("Geometrie parameters")
    param_values: Dict[str, float] = {}
    for p in coil_model.parameters.values():
        if p.is_int:
            val = st.sidebar.slider(
                p.label,
                min_value=int(p.min_value),
                max_value=int(p.max_value),
                value=int(p.default),
                step=int(p.step),
            )
            param_values[p.name] = float(val)
        else:
            val = st.sidebar.slider(
                p.label,
                min_value=float(p.min_value),
                max_value=float(p.max_value),
                value=float(p.default),
                step=float(p.step),
            )
            param_values[p.name] = float(val)

    st.sidebar.subheader("Draad & drive")
    wire_radius_mm = st.sidebar.slider(
        "Draadradius [mm]", 0.1, 3.0, 0.8, 0.1
    )

    logf = st.sidebar.slider("log10(frequency [Hz])", 1.0, 8.0, 5.0, 0.1)
    freq_hz = 10 ** logf
    current_A = st.sidebar.slider(
        "Stroom per fase [A]", 0.1, 2000.0, 10.0, 0.1
    )

    field_metric = st.sidebar.selectbox(
        "Field metric (kleur in 3D-plot)",
        options=[
            "|B|",
            "1 - G (SST gravity dilation)",
            "||g|| (swirl gravity tensor)",
        ],
    )

    B_sat = st.sidebar.slider(
        "B_saturation [T] (voor gravity metric)", 0.5, 20.0, 5.0, 0.5
    )

    # --- geometrie ---
    points_per_turn = 800 if "rodin" in coil_key or "saw_bowl" in coil_key else 400
    polylines = coil_model.build_polylines(param_values, points_per_turn)
    segments = coil_model.build_segments(param_values, points_per_turn)
    wire_length = coil_model.wire_length(param_values, points_per_turn)

    # --- scalar parameters ---
    radius_m = wire_radius_mm * 1e-3
    delta = float(skin_depth_copper(freq_hz))
    R_ac = ac_resistance_round_wire(
        f_hz=freq_hz,
        rho=RHO_CU,
        length_m=wire_length,
        radius_m=radius_m,
    )
    L_H = coil_model.estimate_inductance(param_values, polylines)
    omega = 2.0 * np.pi * freq_hz
    Q = omega * L_H / max(R_ac, 1e-9)

    # simpele parasitaire C
    C_parasitic = 20e-12
    fres_est = 1.0 / (2.0 * np.pi * np.sqrt(L_H * C_parasitic))

    # --- metrics display ---
    st.subheader("Samenvatting coil + draadkeuze")
    c1, c2, c3 = st.columns(3)
    c1.metric("Draadradius", f"{wire_radius_mm:.2f} mm")
    c2.metric("Totale draadlengte", f"{wire_length:.3f} m")
    c3.metric("Skin-diepte δ", f"{delta*1e3:.3f} mm")

    c4, c5, c6 = st.columns(3)
    c4.metric("AC-weerstand R_ac", f"{R_ac:.3f} Ω")
    c5.metric("Inductie L", f"{L_H*1e3:.3f} mH")
    c6.metric("Q-factor bij f", f"{Q:.1f}")

    st.metric("Geschatte eigenresonantie f_res", f"{fres_est/1e3:.1f} kHz")

    # --- 2D footprint ---
    st.subheader("2D projectie van windingen (x–y)")
    pts_mid = 0.5 * (segments[:, 0, :] + segments[:, 1, :])
    fig_xy = px.scatter(
        x=pts_mid[:, 0],
        y=pts_mid[:, 1],
        title="Projectie van spoel in x–y vlak",
        labels={"x": "x [m]", "y": "y [m]"},
    )
    fig_xy.update_yaxes(scaleanchor="x", scaleratio=1)
    st.plotly_chart(fig_xy, use_container_width=True)

    # --- 3D veld ---
    st.subheader("3D veld (Biot–Savart, multi-phase)")

    grid_size = st.sidebar.slider("Grid size per axis", 8, 25, 15, 1)
    span = st.sidebar.slider("Grid span [m] (±)", 0.05, 3.0, 0.3, 0.05)

    xg = np.linspace(-span, span, grid_size)
    yg = np.linspace(-span, span, grid_size)
    zg = np.linspace(-span, span, grid_size)
    X, Y, Z = np.meshgrid(xg, yg, zg)
    eval_pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)

    B_total = np.zeros_like(eval_pts)
    for poly in polylines:
        B_total += compute_field_vectorized(eval_pts, poly, current_A)

    B_mag = np.linalg.norm(B_total, axis=1)

    # --- NIEUW: B op de grid reshape'en ---
    Bx_grid = B_total[:, 0].reshape(X.shape)
    By_grid = B_total[:, 1].reshape(X.shape)
    Bz_grid = B_total[:, 2].reshape(X.shape)

    dx = float(xg[1] - xg[0]) if len(xg) > 1 else 1.0
    dy = float(yg[1] - yg[0]) if len(yg) > 1 else 1.0
    dz = float(zg[1] - zg[0]) if len(zg) > 1 else 1.0

    # Voor performance: swirl-g alleen berekenen wanneer nodig
    if field_metric == "||g|| (swirl gravity tensor)":
        omega_x, omega_y, omega_z = compute_vorticity(
            Bx_grid, By_grid, Bz_grid, dx, dy, dz
        )
        R_swirl = compute_swirl_curvature_tensor(omega_x, omega_y, omega_z)
        g_field = compute_swirl_gravity(omega_x, omega_y, omega_z, R_swirl)  # (3,Nx,Ny,Nz)
        g_mag_grid = np.sqrt(
            g_field[0] ** 2 + g_field[1] ** 2 + g_field[2] ** 2
        )
        g_mag_flat = g_mag_grid.ravel()
    else:
        g_mag_flat = None  # niet gebruikt

    # Kleurkeuze
    if field_metric == "1 - G (SST gravity dilation)":
        G = SSTGravityMetric.compute_gravity_dilation(
            B_field=B_total,
            omega_drive=freq_hz,
            B_saturation=B_sat,
        )
        color_vals = 1.0 - G
        color_label = "1 - G"

    elif field_metric == "||g|| (swirl gravity tensor)":
        color_vals = g_mag_flat
        color_label = "||g|| (swirl gravity tensor)"

    else:
        color_vals = B_mag
        color_label = "|B| [T]"

    df_B = pd.DataFrame(
        {
            "x": eval_pts[:, 0],
            "y": eval_pts[:, 1],
            "z": eval_pts[:, 2],
            "val": color_vals,
        }
    )

    fig_B = px.scatter_3d(
        df_B,
        x="x",
        y="y",
        z="z",
        color="val",
        title=f"Field metric: {color_label}",
    )

    # coil geometry toevoegen
    for poly in polylines:
        fig_B.add_trace(
            go.Scatter3d(
                x=poly[:, 0],
                y=poly[:, 1],
                z=poly[:, 2],
                mode="lines",
                name="coil phase",
            )
        )

    fig_B.update_layout(scene_aspectmode="data")
    st.plotly_chart(fig_B, use_container_width=True)

    st.caption(
        "Architectuur is modulair: voeg nieuwe CoilModel-subclasses toe in coil_geometries "
        "om extra topologieën (Gamma, stacked Starships, mirrored arrays, enz.) in te pluggen. "
        "Field metric kan worden uitgebreid met Beltrami shear / helicity als volgende stap."
    )


def main():
    # Eenvoudige pagina-switcher boven de analyzer
    page = st.sidebar.selectbox(
        "View",
        ["Coil Analyzer", "Magnet Ring + Coil Mixed Field"],
    )

    if page == "Coil Analyzer":
        render_coil_analyzer()
    elif page == "Magnet Ring + Coil Mixed Field":
        render_magnet_ring_view()

if __name__ == "__main__":
    main()