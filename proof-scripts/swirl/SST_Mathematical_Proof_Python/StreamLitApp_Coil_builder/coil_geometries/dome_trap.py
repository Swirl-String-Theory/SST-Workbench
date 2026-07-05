# coil_geometries/dome_trap.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import numpy as np

from .base import CoilModel, CoilParameter, MU_0


def _make_dome_spiral(
        R: float,
        z_start: float,
        z_end: float,
        turns: int,
        chirality: int,
        num_points: int = 1000,
) -> np.ndarray:
    """
    Spiral on a spherical cap between z_start and z_end.
    """
    t = np.linspace(0.0, 1.0, num_points)

    z_local = z_start + (z_end - z_start) * t
    r_local = np.sqrt(np.clip(R**2 - z_local**2, 0.0, None))

    total_angle = 2.0 * np.pi * turns
    theta = total_angle * t * chirality

    x = r_local * np.cos(theta)
    y = r_local * np.sin(theta)
    z = z_local
    return np.stack([x, y, z], axis=1)


@dataclass
class DomeTrapCoil(CoilModel):
    """
    'Diabolo' / dome trap coil:
    Two hemispherical spirals with opposing chirality.
    """
    name: str = "Dome Trap (Opposing Domes)"
    parameters: Dict[str, CoilParameter] = field(default_factory=lambda: {
        "dome_radius_m": CoilParameter(
            name="dome_radius_m", label="Dome radius R [m]",
            default=0.20, min_value=0.05, max_value=0.5, step=0.01
        ),
        "dome_gap_m": CoilParameter(
            name="dome_gap_m", label="Gap tussen domes [m]",
            default=0.05, min_value=0.01, max_value=0.2, step=0.005
        ),
        "dome_layers": CoilParameter(
            name="dome_layers", label="Windingen per dome",
            default=40, min_value=1, max_value=200, step=1, is_int=True
        ),
    })

    def build_polylines(
            self,
            params: Dict[str, float],
            points_per_turn: int = 1000,
    ) -> List[np.ndarray]:
        R = params["dome_radius_m"]
        gap = params["dome_gap_m"]
        turns = int(params["dome_layers"])

        # bottom dome: -R -> -gap/2
        pts_bot = _make_dome_spiral(
            R=R,
            z_start=-R,
            z_end=-gap / 2.0,
            turns=turns,
            chirality=+1,
            num_points=points_per_turn,
        )

        # top dome: +R -> +gap/2, mirrored
        pts_top = _make_dome_spiral(
            R=R,
            z_start=+R,
            z_end=+gap / 2.0,
            turns=turns,
            chirality=-1,
            num_points=points_per_turn,
        )

        return [pts_bot, pts_top]

    def estimate_inductance(
            self,
            params: Dict[str, float],
            polylines: List[np.ndarray],
    ) -> float:
        R = params["dome_radius_m"]
        turns = float(params["dome_layers"])

        L_single = MU_0 * turns**2 * R  # heel grof
        return float(2.0 * L_single)