from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass
class CurveSet:
    points: np.ndarray
    offsets: np.ndarray

    def __post_init__(self):
        self.points = np.asarray(self.points, dtype=float)
        self.offsets = np.asarray(self.offsets, dtype=np.int64)
        if self.points.ndim != 2 or self.points.shape[1] != 3:
            raise ValueError("points must be Nx3")
        if self.offsets.ndim != 1 or len(self.offsets) < 2:
            raise ValueError("offsets must have at least [0,N]")
        if self.offsets[0] != 0 or self.offsets[-1] != len(self.points):
            raise ValueError("offsets do not span points")
        if np.any(np.diff(self.offsets) < 4):
            raise ValueError("every closed component needs at least 4 points")

    @property
    def n_components(self) -> int:
        return len(self.offsets) - 1

    def components(self):
        return [self.points[self.offsets[i]:self.offsets[i+1]] for i in range(self.n_components)]

    @classmethod
    def from_components(cls, comps):
        comps = [np.asarray(c, dtype=float) for c in comps]
        offsets = [0]
        for c in comps:
            offsets.append(offsets[-1] + len(c))
        return cls(np.vstack(comps), np.asarray(offsets, dtype=np.int64))
