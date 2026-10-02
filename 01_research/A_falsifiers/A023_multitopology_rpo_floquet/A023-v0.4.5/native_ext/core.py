from __future__ import annotations
import os, sys
from typing import Any
import numpy as np
from . import _config
from . import fallback
from .dll_search import configure_windows_dll_search
from .sycl_worker import biot_savart as worker_biot_savart, worker_info

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

def native_info(mod=None, probe_sycl_worker=False):
    if mod is None:
        mod = _import_native()
    if mod is None:
        d = fallback.backend_info()
    else:
        try:
            d = dict(mod.backend_info())
        except Exception:
            d = {}
        d['native_loaded'] = True
        d['sycl_compiled'] = bool(getattr(mod, 'sycl_compiled', d.get('sycl_compiled', False)))
        d['openmp_compiled'] = bool(getattr(mod, 'openmp_compiled', d.get('openmp_compiled', False)))
    # v0.4.5: do NOT build/probe the external SYCL worker during ordinary
    # CPU/OpenMP/auto campaigns.  Worker probing can invoke icpx and a GPU
    # runtime and is deliberately opt-in for explicit SYCL runs.
    wi = {'available': False, 'probe_skipped': True}
    if probe_sycl_worker:
        try:
            wi = worker_info(start=False)
        except Exception as exc:
            wi = {'available': False, 'error': f'{type(exc).__name__}: {exc}'}
    d['sycl_worker'] = wi
    d['has_gpu'] = bool(wi.get('available') and wi.get('is_gpu'))
    d['sycl_worker_available'] = bool(wi.get('available'))
    d['sycl_compiled'] = bool(d.get('sycl_compiled', False))
    if wi.get('available'):
        d['sycl_transport'] = wi.get('transport','external_process')
        d['sycl_device_name'] = wi.get('device_name','unknown')
        d['sycl_native_fp64'] = bool(wi.get('fp64',False))
        d['sycl_numeric_role'] = 'confirmatory_fp64' if wi.get('fp64') else 'screening_fp32_only'
    return d

def resolve_backend(requested='auto', mod=None, allow_sycl_cpu=False):
    req = (requested or os.environ.get('SST_BACKEND') or 'auto').lower()
    if req == 'python':
        return 'python'
    if req == 'sycl':
        wi = worker_info(start=False)
        if wi.get('available') and (wi.get('is_gpu') or allow_sycl_cpu):
            return 'sycl-worker'
        raise RuntimeError(f'SYCL requested but external worker is unavailable: {wi}')
    if req in ('openmp','cpu'):
        return 'openmp' if mod is not None else 'python'
    # v0.4.5: auto is deterministic confirmatory host FP64.  It never probes
    # or starts the external GPU worker.  GPU use requires --backend sycl.
    return 'openmp' if mod is not None else 'python'

def biot_savart(points, queries, *, gamma=1.0, core=0.04, backend='auto', allow_sycl_cpu=False, mod=None):
    p = np.ascontiguousarray(points, dtype=float)
    q = np.ascontiguousarray(queries, dtype=float)
    chosen = resolve_backend(backend, mod, allow_sycl_cpu)
    if chosen == 'sycl-worker':
        return worker_biot_savart(p, q, gamma=float(gamma), core=float(core), require_fp64=False)
    if chosen == 'python' or mod is None:
        return fallback.biot_savart(p, q, gamma, core), 'python'
    out = np.asarray(mod.biot_savart(p, q, float(gamma), float(core), False, bool(allow_sycl_cpu)))
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
