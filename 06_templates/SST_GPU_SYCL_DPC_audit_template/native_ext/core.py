from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from . import _config
from .fallback import (
    biot_savart as biot_savart_py,
    circle,
    default_queries,
    min_abs as min_abs_py,
    python_backend_info,
    vec_add as vec_add_py,
)
from .sycl_worker import biot_savart as worker_biot_savart
from .sycl_worker import shutdown_worker, worker_info


def write_json(path: str | Path, data: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def write_csv(path: str | Path, rows: list[dict[str, Any]]) -> None:
    import csv

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with p.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _import_native():
    try:
        _config.ensure_oneapi_dll_directories()
        return __import__(f"{_config.PACKAGE_NAME}.{_config.EXT_BASENAME}", fromlist=["*"])
    except Exception:
        return None


def _load_cpp_backend(*, force_build: bool = False, build_verbose: bool = False, skip_build: bool = False):
    if skip_build:
        return _import_native()
    try:
        from .build_ext_if_needed import build_if_needed

        build_if_needed(force=force_build, verbose=build_verbose)
        return _import_native()
    except Exception as exc:
        print(f"{_config.LOG_PREFIX} native load failed: {exc}", file=sys.stderr)
        return None


def native_info(mod: Any | None, *, probe_sycl_worker: bool = False) -> dict[str, Any]:
    if mod is None:
        info = python_backend_info()
        info["native_loaded"] = False
        info["has_gpu"] = False
    else:
        try:
            info = dict(mod.backend_info())
        except Exception:
            info = {}
        info["native_loaded"] = True
        info["sycl_compiled"] = bool(getattr(mod, "sycl_compiled", info.get("sycl_compiled", False)))
        info["openmp_compiled"] = bool(getattr(mod, "openmp_compiled", info.get("openmp_compiled", False)))
        info["has_gpu"] = False

    wi = worker_info(start=False) if not probe_sycl_worker else worker_info(start=True)
    info["sycl_worker"] = wi
    info["sycl_worker_available"] = bool(wi.get("available"))
    if wi.get("available"):
        info["has_gpu"] = bool(wi.get("is_gpu"))
        info["is_gpu"] = bool(wi.get("is_gpu"))
        info["device_name"] = wi.get("device_name", info.get("device_name"))
        info["fp64"] = bool(wi.get("fp64", False))
        # Treat external worker as the SYCL path (not in-process .pyd).
        info["sycl_compiled"] = True
    return info


def resolve_backend(
    requested: str,
    info: dict[str, Any],
    *,
    allow_sycl_cpu: bool = False,
    strict_sycl: bool = False,
) -> str:
    req = (requested or os.environ.get("SST_BACKEND") or "auto").lower()
    if req == "python":
        return "python"
    has_native = bool(info.get("native_loaded"))

    def sycl_gpu() -> bool:
        return bool(info.get("sycl_worker_available") and (info.get("has_gpu") or info.get("is_gpu")))

    if req == "sycl":
        if sycl_gpu():
            return "sycl"
        if info.get("sycl_worker_available") and allow_sycl_cpu:
            return "sycl"
        raise RuntimeError(
            "SYCL GPU worker required but not visible. Use run_sycl_worker_smoke.cmd / run_arc.cmd "
            "(session setvars, ONEAPI_DEVICE_SELECTOR=level_zero:gpu, SST_SYCL_ALLOW_FP32=1 on Arc)."
        )
    if req == "openmp":
        return "openmp" if has_native else "python"
    if sycl_gpu():
        return "sycl"
    if has_native:
        return "openmp"
    return "python"


def run_tiny(
    a: np.ndarray | None = None,
    b: np.ndarray | None = None,
    *,
    backend: str = "auto",
    allow_sycl_cpu: bool = False,
    force_python: bool = False,
    skip_build: bool = False,
    force_build: bool = False,
    build_verbose: bool = False,
    strict_sycl: bool = False,
) -> dict[str, Any]:
    if a is None:
        a = np.arange(16, dtype=float)
    if b is None:
        b = 2.0 * np.arange(16, dtype=float)
    t0 = time.perf_counter()
    if force_python:
        backend = "python"
    mod = None if force_python else _load_cpp_backend(force_build=force_build, build_verbose=build_verbose, skip_build=skip_build)
    info = native_info(mod, probe_sycl_worker=(backend in ("sycl", "auto")))
    chosen = resolve_backend(backend, info, allow_sycl_cpu=allow_sycl_cpu, strict_sycl=strict_sycl)
    # vec_add stays host/OpenMP (worker only implements Biot-Savart).
    if chosen == "python" or mod is None:
        value = vec_add_py(a, b)
        ms = (time.perf_counter() - t0) * 1000.0
        probe = python_backend_info(last_kernel_ms=ms)
        probe.update({"backend": "python", "value": value.tolist(), "ok": np.allclose(value, np.asarray(a) + np.asarray(b))})
        return probe
    use_host = True
    value = np.asarray(mod.vec_add(np.asarray(a, float), np.asarray(b, float), False, False))
    probe = native_info(mod)
    probe["backend"] = probe.get("last_backend", "openmp" if use_host else chosen)
    probe["value"] = value.tolist()
    probe["ok"] = bool(np.allclose(value, np.asarray(a, float) + np.asarray(b, float)))
    return probe


def run(
    *,
    n_segments: int = 512,
    n_queries: int = 8192,
    gamma: float = 1.0,
    core: float = 1.0,
    backend: str = "auto",
    allow_sycl_cpu: bool = False,
    force_python: bool = False,
    skip_build: bool = False,
    force_build: bool = False,
    build_verbose: bool = False,
    strict_sycl: bool = False,
) -> dict[str, Any]:
    """GPU-first Biot-Savart via external worker; OpenMP/Python on host."""
    points = circle(n_segments)
    queries = default_queries(n_queries)
    if force_python:
        backend = "python"
    if backend == "python" and n_queries * n_segments > 256 * 64:
        print(
            f"{_config.LOG_PREFIX} warning: Python backend on N={n_segments} M={n_queries} is not the GPU path.",
            file=sys.stderr,
        )
    t0 = time.perf_counter()
    mod = None if force_python else _load_cpp_backend(force_build=force_build, build_verbose=build_verbose, skip_build=skip_build)
    info = native_info(mod, probe_sycl_worker=(backend in ("sycl", "auto") or strict_sycl))
    chosen = resolve_backend(backend, info, allow_sycl_cpu=allow_sycl_cpu, strict_sycl=strict_sycl)

    if chosen == "sycl":
        vel, label = worker_biot_savart(points, queries, gamma=float(gamma), core=float(core))
        ms = (time.perf_counter() - t0) * 1000.0
        wi = worker_info()
        probe = {
            "backend": label,
            "sycl_compiled": True,
            "native_loaded": bool(mod is not None),
            "openmp_compiled": bool(info.get("openmp_compiled")),
            "is_gpu": bool(wi.get("is_gpu")),
            "has_gpu": bool(wi.get("is_gpu")),
            "device_name": wi.get("device_name"),
            "fp64": bool(wi.get("fp64", False)),
            "sycl_worker_available": True,
            "transport": wi.get("transport"),
            "n_segments": int(n_segments),
            "n_queries": int(n_queries),
            "velocity_l2": float(np.linalg.norm(vel)),
            "last_kernel_ms": ms,
            "ok": bool(np.isfinite(vel).all()),
        }
        return probe

    if chosen == "python" or mod is None:
        vel = biot_savart_py(points, queries, gamma, core)
        ms = (time.perf_counter() - t0) * 1000.0
        probe = python_backend_info(last_kernel_ms=ms)
        probe.update(
            {
                "backend": "python",
                "n_segments": int(n_segments),
                "n_queries": int(n_queries),
                "velocity_l2": float(np.linalg.norm(vel)),
                "ok": bool(np.isfinite(vel).all()),
            }
        )
        return probe

    vel = np.asarray(mod.biot_savart(points, queries, float(gamma), float(core), False, False))
    probe = native_info(mod)
    probe["backend"] = probe.get("last_backend", chosen)
    probe["n_segments"] = int(n_segments)
    probe["n_queries"] = int(n_queries)
    probe["velocity_l2"] = float(np.linalg.norm(vel))
    probe["ok"] = bool(np.isfinite(vel).all())
    probe["is_gpu"] = False
    return probe


def run_min_abs(
    x: np.ndarray,
    *,
    backend: str = "auto",
    allow_sycl_cpu: bool = False,
    force_python: bool = False,
    skip_build: bool = False,
    force_build: bool = False,
    build_verbose: bool = False,
) -> dict[str, Any]:
    if force_python:
        backend = "python"
    mod = None if force_python else _load_cpp_backend(force_build=force_build, build_verbose=build_verbose, skip_build=skip_build)
    info = native_info(mod)
    # min_abs is host-only in this template.
    chosen = "python" if force_python or mod is None else ("openmp" if info.get("native_loaded") else "python")
    if backend == "python":
        chosen = "python"
    xx = np.asarray(x, dtype=float).reshape(-1)
    if chosen == "python" or mod is None:
        value = min_abs_py(xx)
        return {"backend": "python", "value": value, "ok": True}
    value = float(mod.min_abs(xx, False, False))
    probe = native_info(mod)
    probe["backend"] = probe.get("last_backend", chosen)
    probe["value"] = value
    probe["ok"] = np.isfinite(value)
    return probe


def run_audit(
    *,
    n_segments: int = 512,
    n_queries: int = 8192,
    gamma: float = 1.0,
    core: float = 1.0,
    backend: str = "auto",
    allow_sycl_cpu: bool = False,
    force_python: bool = False,
    skip_build: bool = False,
    force_build: bool = False,
    build_verbose: bool = False,
    strict_sycl: bool = False,
) -> dict[str, Any]:
    probe = run(
        n_segments=n_segments,
        n_queries=n_queries,
        gamma=gamma,
        core=core,
        backend=backend,
        allow_sycl_cpu=allow_sycl_cpu,
        force_python=force_python,
        skip_build=skip_build,
        force_build=force_build,
        build_verbose=build_verbose,
        strict_sycl=strict_sycl,
    )
    return {
        "audit_name": "SST GPU SYCL/DPC++ biot_savart template",
        "probe": probe,
        "ok": bool(probe.get("ok")),
    }


def run_sweep(
    query_counts: list[int],
    *,
    n_segments: int = 256,
    backend: str = "auto",
    allow_sycl_cpu: bool = False,
    force_python: bool = False,
    skip_build: bool = False,
    force_build: bool = False,
    build_verbose: bool = False,
    strict_sycl: bool = False,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    first = True
    for m in query_counts:
        row = run(
            n_segments=n_segments,
            n_queries=int(m),
            backend=backend,
            allow_sycl_cpu=allow_sycl_cpu,
            force_python=force_python,
            skip_build=skip_build if not first else skip_build,
            force_build=force_build if first else False,
            build_verbose=build_verbose if first else False,
            strict_sycl=strict_sycl,
        )
        first = False
        row["ok"] = bool(row.get("ok"))
        rows.append(row)
    return rows


def run_all_checks(
    *,
    out_dir: str | Path | None = None,
    backend: str = "auto",
    allow_sycl_cpu: bool = False,
    force_python: bool = False,
    force_build: bool = False,
    strict_sycl: bool = False,
) -> dict[str, Any]:
    out = Path(out_dir) if out_dir is not None else _config.default_output_dir()
    out.mkdir(parents=True, exist_ok=True)

    smoke_py = run_audit(n_segments=32, n_queries=16, force_python=True, skip_build=True)
    write_json(out / "smoke_python.json", smoke_py)

    smoke_native = None
    smoke_sycl = None
    heavy = None
    if not force_python:
        smoke_native = run_audit(
            n_segments=64,
            n_queries=32,
            backend="openmp",
            force_build=force_build,
            allow_sycl_cpu=allow_sycl_cpu,
        )
        write_json(out / "smoke_openmp.json", smoke_native)
        try:
            smoke_sycl = run_audit(
                n_segments=128,
                n_queries=256,
                backend="sycl",
                allow_sycl_cpu=allow_sycl_cpu,
                strict_sycl=strict_sycl or backend == "sycl",
            )
            write_json(out / "smoke_sycl.json", smoke_sycl)
        except Exception as exc:
            write_json(out / "smoke_sycl.json", {"ok": False, "error": str(exc)})
            if strict_sycl or backend == "sycl":
                raise
        if smoke_sycl and smoke_sycl.get("ok") and smoke_sycl.get("probe", {}).get("is_gpu"):
            heavy = run_audit(
                n_segments=512,
                n_queries=8192,
                backend="sycl",
                allow_sycl_cpu=False,
                strict_sycl=True,
            )
            write_json(out / "heavy_sycl.json", heavy)

    sweep_counts = [256, 1024, 2048] if not force_python else [8, 16]
    sweep_backend = "python" if force_python else backend
    sweep = run_sweep(
        sweep_counts,
        n_segments=64 if force_python else 256,
        backend=sweep_backend,
        allow_sycl_cpu=allow_sycl_cpu,
        force_python=force_python,
        skip_build=force_python,
        force_build=False,
        strict_sycl=strict_sycl,
    )
    write_json(out / "sweep.json", sweep)
    write_csv(out / "sweep.csv", sweep)

    timings = {
        "python_ms": smoke_py["probe"].get("last_kernel_ms"),
        "openmp_ms": None if smoke_native is None else smoke_native["probe"].get("last_kernel_ms"),
        "sycl_ms": None if smoke_sycl is None else smoke_sycl.get("probe", {}).get("last_kernel_ms"),
        "heavy_sycl_ms": None if heavy is None else heavy.get("probe", {}).get("last_kernel_ms"),
    }
    summary = {
        "audit_name": "SST GPU SYCL/DPC++ template full check",
        "out_dir": str(out),
        "smoke_python_ok": smoke_py["ok"],
        "smoke_openmp_ok": None if smoke_native is None else smoke_native["ok"],
        "smoke_sycl_ok": None if smoke_sycl is None else smoke_sycl.get("ok"),
        "heavy_sycl_ok": None if heavy is None else heavy.get("ok"),
        "heavy_is_gpu": None if heavy is None else bool(heavy.get("probe", {}).get("is_gpu")),
        "sycl_backend_label": None if smoke_sycl is None else smoke_sycl.get("probe", {}).get("backend"),
        "sweep_ok": all(r.get("ok") for r in sweep),
        "timings_ms": timings,
        "ok": bool(smoke_py["ok"] and (force_python or (smoke_native and smoke_native["ok"])) and all(r.get("ok") for r in sweep)),
    }
    if strict_sycl:
        summary["ok"] = bool(
            summary["ok"]
            and smoke_sycl
            and smoke_sycl.get("ok")
            and smoke_sycl.get("probe", {}).get("is_gpu")
        )
    write_json(out / "audit_summary.json", summary)
    try:
        shutdown_worker()
    except Exception:
        pass
    return summary
