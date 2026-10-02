import os
import numpy as np
from . import reference


def _native_module():
    mode = os.environ.get("SST_BACKEND", "auto").lower()
    if mode == "python":
        return None
    try:
        import triadic_native
        return triadic_native
    except Exception as exc:
        if mode == "native":
            raise RuntimeError(
                "SST_BACKEND=native was requested, but triadic_native could not be imported. "
                "Build the extension first with build_native.cmd."
            ) from exc
        return None


def backend_name():
    return "native" if _native_module() is not None else "python"


def decompose_gradient(grad):
    native = _native_module()
    arr = np.asarray(grad, dtype=float)
    if native is None:
        return reference.decompose_gradient(arr)
    shape = arr.shape[:-2]
    flat = np.ascontiguousarray(arr.reshape((-1, 3, 3)))
    S, omega, div = native.decompose_gradient(flat)
    return (
        np.asarray(S).reshape(shape + (3, 3)),
        np.asarray(omega).reshape(shape + (3,)),
        np.asarray(div).reshape(shape),
    )


def invariants(u, omega, strain):
    native = _native_module()
    if native is None:
        return reference.invariants(u, omega, strain)
    shape = np.asarray(u).shape[:-1]
    uf = np.ascontiguousarray(np.asarray(u, dtype=float).reshape((-1, 3)))
    wf = np.ascontiguousarray(np.asarray(omega, dtype=float).reshape((-1, 3)))
    sf = np.ascontiguousarray(np.asarray(strain, dtype=float).reshape((-1, 3, 3)))
    vals = np.asarray(native.invariants(uf, wf, sf))
    return {
        "speed2": vals[:, 0].reshape(shape),
        "omega2": vals[:, 1].reshape(shape),
        "strain2": vals[:, 2].reshape(shape),
        "helicity": vals[:, 3].reshape(shape),
    }
