from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import numpy as np

@dataclass(frozen=True)
class FourierComponent:
    index: int
    declared_length: float
    A: np.ndarray
    B: np.ndarray

@dataclass(frozen=True)
class IdealLink:
    link_id: str
    conway: str
    diameter: float
    components: tuple[FourierComponent, ...]

@dataclass(frozen=True)
class SampledComponent:
    t: np.ndarray
    r: np.ndarray
    d1: np.ndarray
    d2: np.ndarray
    d3: np.ndarray
    component: FourierComponent

def jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value
