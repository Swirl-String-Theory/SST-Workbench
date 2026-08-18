from __future__ import annotations

import numpy as np
import pytest

from native_ext.core import native_info, resolve_backend, run, run_min_abs
from native_ext.fallback import python_backend_info


def test_backend_info_python_keys():
    info = python_backend_info()
    for key in ("backend", "sycl_compiled", "openmp_compiled", "is_gpu", "device_name", "queue_reused", "last_kernel_ms"):
        assert key in info
    assert info["backend"] == "python"
    assert info["is_gpu"] is False


def test_resolve_backend_gpu_first():
    info = {
        "native_loaded": True,
        "sycl_compiled": True,
        "openmp_compiled": True,
        "has_gpu": True,
        "is_gpu": True,
    }
    assert resolve_backend("auto", info) == "sycl"
    assert resolve_backend("openmp", info) == "openmp"
    assert resolve_backend("python", info) == "python"


def test_resolve_backend_sycl_without_gpu_raises():
    info = {"native_loaded": True, "sycl_compiled": True, "has_gpu": False, "is_gpu": False}
    with pytest.raises(RuntimeError):
        resolve_backend("sycl", info, allow_sycl_cpu=False)


def test_run_min_abs_python():
    x = np.array([-4.0, 1.5, 9.0])
    row = run_min_abs(x, force_python=True, skip_build=True)
    assert row["backend"] == "python"
    assert row["value"] == 1.5


def test_backend_info_keys(native_mod):
    if native_mod is None:
        pytest.skip("native extension not built")
    info = native_info(native_mod)
    for key in ("sycl_compiled", "openmp_compiled", "is_gpu", "device_name", "last_kernel_ms"):
        assert key in info
    if info.get("sycl_compiled") and info.get("has_gpu"):
        assert info["is_gpu"] or info["has_gpu"]


def test_sycl_heavy_or_skip(native_mod):
    if native_mod is None:
        pytest.skip("native extension not built")
    info = native_info(native_mod)
    if not (info.get("sycl_compiled") and info.get("has_gpu")):
        pytest.skip("no SYCL GPU")
    probe = run(n_segments=256, n_queries=2048, backend="sycl", skip_build=True, strict_sycl=True)
    assert probe["backend"] == "sycl"
    assert probe["is_gpu"] is True
    assert probe["ok"] is True
    assert float(probe.get("last_kernel_ms", 0)) >= 0.0
