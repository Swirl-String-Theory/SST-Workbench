from __future__ import annotations
import os
import native_ext.core as core


def test_normal_host_import_does_not_register_oneapi_dlls(monkeypatch):
    monkeypatch.delenv('SST_ENABLE_UNSAFE_INPROC_SYCL', raising=False)
    def forbidden(*args, **kwargs):
        raise AssertionError('oneAPI DLL registration must not run for host/OpenMP import')
    monkeypatch.setattr(core, 'configure_windows_dll_search', forbidden)
    # A missing extension is fine in this source-tree test; the invariant is that
    # the forbidden DLL registration hook is not touched.
    core._import_native()


def test_legacy_unsafe_inproc_sycl_keeps_explicit_registration(monkeypatch):
    monkeypatch.setenv('SST_ENABLE_UNSAFE_INPROC_SYCL', '1')
    called={'n':0}
    def marker(*args, **kwargs):
        called['n'] += 1
        return []
    monkeypatch.setattr(core, 'configure_windows_dll_search', marker)
    core._import_native()
    assert called['n'] == 1
