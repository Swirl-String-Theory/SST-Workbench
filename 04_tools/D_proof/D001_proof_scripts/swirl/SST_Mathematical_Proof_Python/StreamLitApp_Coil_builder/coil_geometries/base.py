# coil_geometries/base.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import numpy as np

MU_0 = 4.0 * np.pi * 1e-7  # H/m


@dataclass
class CoilParameter:
    """
    Generic parameter description for a coil model.
    """
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
    Abstract base class for coil geometries.

    Subclasses must implement:
      - build_polylines(params, points_per_turn) -> List[np.ndarray] (each (N,3))
      - estimate_inductance(params, polylines) -> float [H]

    Helpers:
      - build_segments(...) -> (M,2,3) segments
      - wire_length(...) -> total wire length [m]
    """
    name: str = "base"
    parameters: Dict[str, CoilParameter] = field(default_factory=dict)

    # ---------- required API ----------

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

    # ---------- helpers ----------

    def build_segments(
            self,
            params: Dict[str, float],
            points_per_turn: int = 200
    ) -> np.ndarray:
        polylines = self.build_polylines(params, points_per_turn)
        segs = []
        for poly in polylines:
            seg = np.stack([poly[:-1], poly[1:]], axis=1)  # (N-1, 2, 3)
            segs.append(seg)
        return np.concatenate(segs, axis=0)

    def wire_length(
            self,
            params: Dict[str, float],
            points_per_turn: int = 200
    ) -> float:
        polylines = self.build_polylines(params, points_per_turn)
        total = 0.0
        for poly in polylines:
            dl = np.diff(poly, axis=0)
            total += np.linalg.norm(dl, axis=1).sum()
        return float(total)