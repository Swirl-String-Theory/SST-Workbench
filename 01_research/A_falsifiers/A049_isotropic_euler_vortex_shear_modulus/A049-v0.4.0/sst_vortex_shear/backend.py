import os
import numpy as np
from . import reference
from .filaments import filament_energy_python


def _native_module():
    mode = os.environ.get("SST_BACKEND", "auto").lower()
    if mode == "python":
        return None
    try:
        import vortex_shear_native
        return vortex_shear_native
    except Exception as exc:
        if mode == "native":
            raise RuntimeError("SST_BACKEND=native requested but vortex_shear_native is unavailable") from exc
        return None


def backend_name():
    return "native" if _native_module() is not None else "python"


def energy_ratio_general(nvec, omega_dir, deformation):
    native = _native_module()
    if native is None:
        return reference.energy_ratio_general(nvec, omega_dir, deformation)
    return float(native.energy_ratio_general(
        np.ascontiguousarray(nvec, dtype=float),
        np.ascontiguousarray(omega_dir, dtype=float),
        np.ascontiguousarray(deformation, dtype=float),
    ))


def cross_product(a, b):
    native = _native_module()
    aa = np.asarray(a, dtype=float); bb = np.asarray(b, dtype=float)
    if native is None:
        return np.cross(aa, bb)
    shape = np.broadcast_shapes(aa.shape, bb.shape)
    if shape[-1] != 3:
        raise ValueError("cross_product expects final dimension 3")
    A = np.ascontiguousarray(np.broadcast_to(aa, shape).reshape(-1, 3))
    B = np.ascontiguousarray(np.broadcast_to(bb, shape).reshape(-1, 3))
    return np.asarray(native.cross_product(A, B)).reshape(shape)


def filament_energy(cell, circulations=(1.0,1.0), core_radius=0.18):
    native = _native_module()
    pts = np.ascontiguousarray(cell, dtype=float)
    circs = np.ascontiguousarray(circulations, dtype=float)
    if native is None:
        return filament_energy_python(pts, circs, core_radius)
    return float(native.filament_energy(pts, circs, float(core_radius)))
