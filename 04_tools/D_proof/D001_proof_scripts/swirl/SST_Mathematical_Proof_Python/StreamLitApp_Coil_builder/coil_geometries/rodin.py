# coil_geometries/rodin.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import numpy as np

from .base import CoilModel, CoilParameter, MU_0


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
    Single Rodin/torus-knot phase polyline.
    direction = +1 (bijv. CCW), -1 (mirror).
    """
    theta = np.linspace(0, 2 * np.pi * p, num_points)
    phi = (direction * (q / p) * theta) + phase_shift_angle

    x = (R + r * np.cos(phi)) * np.cos(theta)
    y = (R + r * np.cos(phi)) * np.sin(theta)
    z = r * np.sin(phi)
    return np.stack([x, y, z], axis=1)


@dataclass
class Rodin3PhaseSingle(CoilModel):
    """
    Single 3-phase Rodin coil (all phases same chirality).
    """
    name: str = "Rodin 3-Phase (single)"
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
        for shift in shifts:
            polylines.append(
                generate_rodin_phase(
                    R=R, r=r, p=p, q=q,
                    phase_shift_angle=shift,
                    direction=+1,
                    num_points=points_per_turn,
                )
            )
        return polylines

    def estimate_inductance(
            self,
            params: Dict[str, float],
            polylines: List[np.ndarray],
    ) -> float:
        # Ruwe torus-solenoïde benadering
        R = params["R_major_m"]
        r_ratio = params["r_ratio"]
        p = float(params["p"])
        q = float(params["q"])

        R_torus = R
        A = np.pi * (R * r_ratio) ** 2
        L_len = 2.0 * np.pi * R_torus
        N_eff = p * q
        L = MU_0 * N_eff**2 * A / L_len
        return float(L)


@dataclass
class Rodin3PhaseDouble(CoilModel):
    """
    Double 3-phase Rodin CW & CCW (6 polylines totaal).
    """
    name: str = "Rodin 3-Phase (double CW/CCW)"
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

        # CW (+)
        for shift in shifts:
            polylines.append(
                generate_rodin_phase(
                    R=R, r=r, p=p, q=q,
                    phase_shift_angle=shift,
                    direction=+1,
                    num_points=points_per_turn,
                )
            )

        # CCW (−)
        for shift in shifts:
            polylines.append(
                generate_rodin_phase(
                    R=R, r=r, p=p, q=q,
                    phase_shift_angle=shift,
                    direction=-1,
                    num_points=points_per_turn,
                )
            )

        return polylines

    def estimate_inductance(
            self,
            params: Dict[str, float],
            polylines: List[np.ndarray],
    ) -> float:
        # Zelfde formula als single, maar ~2x
        R = params["R_major_m"]
        r_ratio = params["r_ratio"]
        p = float(params["p"])
        q = float(params["q"])

        R_torus = R
        A = np.pi * (R * r_ratio) ** 2
        L_len = 2.0 * np.pi * R_torus
        N_eff = p * q
        L_single = MU_0 * N_eff**2 * A / L_len
        return float(2.0 * L_single)