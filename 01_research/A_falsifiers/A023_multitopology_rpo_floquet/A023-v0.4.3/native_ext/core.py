from __future__ import annotations
import os, sys
from typing import Any
import numpy as np
from . import _config
from . import fallback
from .dll_search import configure_windows_dll_search

def _import_native():
    configure_windows_dll_search(verbose=False)
    try:
        return __import__(f"{_config.PACKAGE_NAME}.{_config.EXT_BASENAME}", fromlist=['*'])
    except Exception:
        return None

def load_native(force_build=False, build_verbose=False, skip_build=False):
    if not skip_build:
        try:
            from .build_ext_if_needed import build_if_needed
            build_if_needed(force=force_build, verbose=build_verbose)
        except Exception as exc:
            print(f"{_config.LOG_PREFIX} build/load warning: {exc}", file=sys.stderr)
    return _import_native()

def native_info(mod=None):
    if mod is None:
        mod = _import_native()
    if mod is None:
        return fallback.backend_info()
    try:
        d = dict(mod.backend_info())
    except Exception:
        d = {}
    d['native_loaded'] = True
    d['sycl_compiled'] = bool(getattr(mod, 'sycl_compiled', d.get('sycl_compiled', False)))
    d['openmp_compiled'] = bool(getattr(mod, 'openmp_compiled', d.get('openmp_compiled', False)))
    try:
        d['has_gpu'] = bool(mod.probe_sycl_gpu())
    except Exception:
        d['has_gpu'] = bool(d.get('is_gpu', False))
    return d

def resolve_backend(requested='auto', mod=None, allow_sycl_cpu=False):
    req = (requested or os.environ.get('SST_BACKEND') or 'auto').lower()
    info = native_info(mod)
    if req == 'python':
        return 'python'
    if mod is None:
        if req == 'sycl':
            raise RuntimeError('SYCL requested but native extension is unavailable.')
        return 'python'
    if req == 'sycl':
        if info.get('sycl_compiled') and (info.get('has_gpu') or info.get('is_gpu') or allow_sycl_cpu):
            return 'sycl'
        raise RuntimeError('SYCL requested but no usable SYCL device is visible.')
    if req in ('openmp','cpu'):
        return 'openmp'
    if info.get('sycl_compiled') and (info.get('has_gpu') or info.get('is_gpu')):
        return 'sycl'
    return 'openmp'

def biot_savart(points, queries, *, gamma=1.0, core=0.04, backend='auto', allow_sycl_cpu=False, mod=None):
    p = np.ascontiguousarray(points, dtype=float)
    q = np.ascontiguousarray(queries, dtype=float)
    chosen = resolve_backend(backend, mod, allow_sycl_cpu)
    if chosen == 'python' or mod is None:
        return fallback.biot_savart(p, q, gamma, core), 'python'
    out = np.asarray(mod.biot_savart(p, q, float(gamma), float(core), chosen == 'sycl', bool(allow_sycl_cpu)))
    return out, chosen

def centerline_split(points, labels, *, gamma=1.0, core=0.04, local_span=4, mod=None):
    p = np.ascontiguousarray(points, dtype=float)
    lab = np.ascontiguousarray(labels, dtype=np.int32)
    if mod is None:
        d = fallback.centerline_split(p, lab, gamma, core, local_span)
        return d, 'python'
    d = mod.centerline_split(p, lab, float(gamma), float(core), int(local_span))
    return {k: np.asarray(v) for k,v in dict(d).items()}, 'openmp/serial'

def min_nonlocal_distance(points, *, skip=8, mod=None):
    p = np.ascontiguousarray(points, dtype=float)
    if mod is None:
        return fallback.min_nonlocal_distance(p, skip)
    return dict(mod.min_nonlocal_distance(p, int(skip)))
