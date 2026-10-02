"""SYCL external worker helpers."""

from __future__ import annotations

from native_ext.sycl_worker import EXE, probe_worker


def test_worker_exe_path_under_build():
    assert EXE.name.startswith("sst_sycl_worker")
    assert EXE.parent.name == "build"


def test_probe_worker_dict_shape():
    info = probe_worker(force_build=False, verbose=False)
    assert isinstance(info, dict)
    assert "available" in info
    if info.get("available"):
        assert "device_name" in info
        assert "is_gpu" in info
        assert "fp64" in info
