from __future__ import annotations
import os
import numpy as np
from . import reference

try:
    from . import _native as _N
    HAVE_NATIVE = True
except Exception:
    _N = None
    HAVE_NATIVE = False


def backend_name() -> str:
    return "cpp-pybind11" if HAVE_NATIVE else "python-numpy"


def require_native() -> None:
    if not HAVE_NATIVE:
        raise RuntimeError("Native C++ backend required but sst_einstein._native is unavailable")


def set_threads(n: int | None = None) -> int:
    if n is None:
        n = int(os.environ.get("SST_NATIVE_THREADS", "0") or 0)
    if HAVE_NATIVE and n > 0:
        return int(_N.set_threads(int(n)))
    return int(n)


def biot_savart_velocity(points, core, gamma=1.0, uniform_velocity=(0.,0.,0.)):
    if HAVE_NATIVE:
        return _N.biot_savart_velocity(np.asarray(points,float), float(core), float(gamma), np.asarray(uniform_velocity,float))
    return reference.biot_savart_velocity(points, core, gamma, uniform_velocity)


def filament_energy(points, core, rho=1.0, gamma=1.0):
    if HAVE_NATIVE:
        return float(_N.filament_energy(np.asarray(points,float), float(core), float(rho), float(gamma)))
    return reference.filament_energy(points, core, rho, gamma)


def impulse(points, rho=1.0, gamma=1.0):
    if HAVE_NATIVE:
        return np.asarray(_N.impulse(np.asarray(points,float), float(rho), float(gamma)))
    return reference.impulse(points, rho, gamma)


def curvature(points):
    if HAVE_NATIVE:
        return np.asarray(_N.curvature(np.asarray(points,float)))
    return reference.curvature(points)


def rk4_step(points, dt, core, gamma=1.0, uniform_velocity=(0.,0.,0.)):
    if HAVE_NATIVE:
        return _N.rk4_step(np.asarray(points,float), float(dt), float(core), float(gamma), np.asarray(uniform_velocity,float))
    return reference.rk4_step(points, dt, core, gamma, uniform_velocity)
