# coil_geometries/__init__.py
from .base import CoilModel, CoilParameter, MU_0
from .rodin import Rodin3PhaseSingle, Rodin3PhaseDouble
from .dome_trap import DomeTrapCoil
from .saw_bowl import SawBowlCoil

__all__ = [
    "CoilModel",
    "CoilParameter",
    "MU_0",
    "Rodin3PhaseSingle",
    "Rodin3PhaseDouble",
    "DomeTrapCoil",
    "SawBowlCoil",
]