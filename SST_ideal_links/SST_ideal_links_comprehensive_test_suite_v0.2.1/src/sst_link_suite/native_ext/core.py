from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass, replace
from types import ModuleType
from typing import Any
import numpy as np

from . import _config
from .build_ext_if_needed import build_if_needed, extension_path, source_hash


class NativeBackendError(RuntimeError):
    pass


@dataclass(frozen=True)
class BackendOptions:
    require_native: bool = False
    force_python: bool = False
    skip_build: bool = False
    force_build: bool = False
    build_verbose: bool = False


def _import_native(force_build: bool, skip_build: bool, build_verbose: bool) -> ModuleType | None:
    try:
        if not skip_build:
            build_if_needed(force=force_build, verbose=build_verbose)
        importlib.invalidate_caches()
        return importlib.import_module(f"{_config.PACKAGE_NAME}.{_config.EXT_BASENAME}")
    except Exception as exc:
        if build_verbose:
            print(f"{_config.LOG_PREFIX} native import failed: {exc}", file=sys.stderr)
        return None


def resolve_backend(options: BackendOptions) -> tuple[ModuleType, str]:
    if options.require_native and options.force_python:
        raise NativeBackendError("--require-native and --force-python are mutually exclusive")
    if not options.force_python:
        native = _import_native(options.force_build, options.skip_build, options.build_verbose)
        if native is not None:
            return native, "cpp"
    if options.require_native:
        raise NativeBackendError(
            "Native pybind11 backend is required but unavailable. "
            "Install pybind11 and a C++17 compiler, then run the strict build command."
        )
    from . import fallback
    return fallback, "python"


def backend_status(options: BackendOptions) -> dict[str, Any]:
    # Status must not re-force a rebuild: on Windows the loaded .pyd cannot be
    # unlinked/replaced in-process (PermissionError), which previously turned a
    # successful --force-build into NativeBackendError on the second resolve.
    module, name = resolve_backend(replace(options, force_build=False))
    return {
        "backend": name,
        "native_required": options.require_native,
        "force_python": options.force_python,
        "extension_path": str(extension_path()),
        "extension_exists": extension_path().exists(),
        "source_hash": source_hash(),
        "build_info": dict(module.build_info()),
    }


def velocity_at_points(
    evaluation_points: np.ndarray,
    source_points: np.ndarray,
    gamma: float,
    epsilon: float,
    same_curve: bool,
    local_skip: int,
    options: BackendOptions,
) -> tuple[np.ndarray, str]:
    module, name = resolve_backend(options)
    value = module.velocity_at_points(
        np.ascontiguousarray(evaluation_points, dtype=float),
        np.ascontiguousarray(source_points, dtype=float),
        float(gamma), float(epsilon), bool(same_curve), int(local_skip),
    )
    return np.asarray(value), name


def link_velocity_batch(
    curves: list[np.ndarray],
    sign_matrix: np.ndarray,
    epsilon: float,
    local_skip: int,
    options: BackendOptions,
) -> tuple[list[np.ndarray], str]:
    module, name = resolve_backend(options)
    values = module.link_velocity_batch(
        [np.ascontiguousarray(c, dtype=float) for c in curves],
        np.ascontiguousarray(sign_matrix, dtype=float),
        float(epsilon), int(local_skip),
    )
    return [np.asarray(x) for x in values], name


def gauss_linking_matrix(curves: list[np.ndarray], options: BackendOptions) -> tuple[np.ndarray, str]:
    module, name = resolve_backend(options)
    value = module.gauss_linking_matrix([np.ascontiguousarray(c, dtype=float) for c in curves])
    return np.asarray(value), name


def neumann_coupling_matrices(
    curves: list[np.ndarray],
    epsilons: list[float] | np.ndarray,
    local_skip: int,
    options: BackendOptions,
) -> tuple[np.ndarray, str]:
    module, name = resolve_backend(options)
    value = module.neumann_coupling_matrices(
        [np.ascontiguousarray(c, dtype=float) for c in curves],
        np.ascontiguousarray(epsilons, dtype=float),
        int(local_skip),
    )
    return np.asarray(value), name
