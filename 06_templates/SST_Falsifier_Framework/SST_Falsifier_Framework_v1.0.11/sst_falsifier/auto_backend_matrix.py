"""Framework 1.0.11: automatic *diagnostic* multi-backend matrix.

Software/device probes cannot qualify science. Only experiment/backend_matrix.py
may supply falsifier-specific scientific evidence, with actual backend and hashes.
Never silently fall back from requested GPU to CPU.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import traceback
from typing import Any

BACKENDS = ('py', 'cpp', 'gpu')
SCHEMA = 'SST-AUTO-BACKEND-MATRIX-1'


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _python_probe() -> dict:
    try:
        import numpy as np
        x = np.ones((8, 8, 8), dtype=np.float64)
        y = np.fft.fftn(x)
        ok = y.shape == x.shape and np.isfinite(y).all() and abs(y[0,0,0] - 512.0) < 1e-10
        return {'available': bool(ok), 'status': 'DEVICE_READY' if ok else 'BLOCKED',
                'implementation': 'numpy.fft.fftn', 'precision': str(y.dtype),
                'numpy_version': np.__version__, 'python': sys.version.split()[0],
                'device': 'cpu', 'scientific_execution': False}
    except Exception as e:
        return {'available': False, 'status': 'BLOCKED', 'error': f'{type(e).__name__}: {e}', 'scientific_execution': False}


def _cpp_probe(root: Path) -> dict:
    try:
        spec = importlib.util.find_spec('pybind11')
        sources = sorted((root / 'native' / 'cpp').glob('*.cpp')) if (root/'native'/'cpp').exists() else []
        extensions = sorted((root / 'native_ext').glob('_sst_native*.pyd')) + sorted((root / 'native_ext').glob('_sst_native*.so'))
        abi_tag = (getattr(sys.implementation, 'cache_tag', '') or '').replace('cpython-', 'cp')
        matching = [f for f in extensions if abi_tag in f.name or (platform.system() != 'Windows' and f.name.endswith('.so'))]
        build_result = None
        # The framework's own cached pybind11 builder compiles an existing instance
        # source when the ABI-matching extension is missing or stale. It never
        # fabricates a generic native science implementation.
        if spec is not None and (root/'native'/'cpp'/'native.cpp').is_file() and \
                os.environ.get('SST_FALSIFIER_DISABLE_CPP_AUTOBUILD','0') != '1':
            try:
                from .native_build import build_pybind
                build = build_pybind(root, verbose=False)
                build_result = build.to_dict()
                extensions = sorted((root/'native_ext').glob('_sst_native*.pyd')) + sorted((root/'native_ext').glob('_sst_native*.so'))
                matching = [f for f in extensions if abi_tag in f.name or (platform.system() != 'Windows' and f.name.endswith('.so'))]
                if not build.success:
                    matching = []
            except Exception as e:
                build_result = {'success': False, 'error': f'{type(e).__name__}: {e}'}
                matching = []
        ready = bool(spec and matching)
        return {'available': ready, 'status': 'DEVICE_READY' if ready else 'BLOCKED','build': build_result,
                'pybind11_installed': spec is not None, 'native_source_files':
                    [{'name': p.name, 'sha256': _hash(p)} for p in sources],
                'compiled_modules': [{'name': p.name, 'sha256': _hash(p)} for p in matching],
                'python_abi': abi_tag, 'scientific_execution': False,
                'note': 'Presence is not an executed C++ kernel or physics parity. ABI-matching compiled native module required.'}
    except Exception as e:
        return {'available': False, 'status': 'BLOCKED', 'error': f'{type(e).__name__}: {e}', 'scientific_execution': False}


def _gpu_probe() -> dict:
    try:
        import torch
        version = str(torch.__version__)
        xpu = getattr(torch.version, 'xpu', None)
        if not xpu or not hasattr(torch, 'xpu') or not torch.xpu.is_available():
            return {'available': False, 'status': 'BLOCKED', 'torch_version': version,
                    'xpu_build': xpu, 'reason': 'XPU-enabled PyTorch/device unavailable', 'scientific_execution': False}
        if torch.xpu.device_count() < 1:
            return {'available': False, 'status': 'BLOCKED', 'reason': 'No XPU device', 'scientific_execution': False}
        data = torch.ones((8,8,8), dtype=torch.float32, device='xpu:0')
        transformed = torch.fft.fftn(data)
        torch.xpu.synchronize()
        value = float(transformed[0,0,0].real.cpu().item())
        valid = transformed.device.type == 'xpu' and transformed.dtype == torch.complex64 and abs(value - 512.0) < 0.02
        name = str(torch.xpu.get_device_name(0))
        return {'available': bool(valid), 'status': 'DEVICE_READY' if valid else 'BLOCKED',
                'device': name, 'device_type': str(transformed.device),
                'torch_version': version, 'xpu_build': str(xpu),
                'fft_dtype': str(transformed.dtype), 'fft_dc_value': value,
                'precision': 'FP32 / complex64', 'scientific_execution': False,
                'note': 'FP32 FFT device smoke; does not verify complete solver, FP64, or hydrodynamics.'}
    except Exception as e:
        return {'available': False, 'status': 'BLOCKED', 'error': f'{type(e).__name__}: {e}', 'scientific_execution': False}


def probe_all(root: str | Path) -> dict[str, dict]:
    root = Path(root).resolve()
    return {'py': _python_probe(), 'cpp': _cpp_probe(root), 'gpu': _gpu_probe()}


def _validate_record(name: str, payload: Any, device_probe: dict) -> dict:
    """Fail closed: without observed execution and independent comparison, no scientific PASS."""
    if not isinstance(payload, dict):
        return {'status': 'UNIMPLEMENTED', 'scientific_execution': False, 'reason': 'No scientific adapter record'}
    actual = str(payload.get('actual_backend', '')).lower()
    names = {'py': ('py', 'python', 'numpy', 'scipy'), 'cpp': ('cpp', 'c++', 'pybind11', 'openmp'),
             'gpu': ('gpu', 'xpu', 'arc', 'torch-xpu', 'sycl')}
    executed = payload.get('executed') is True
    if not executed or not any(x in actual for x in names[name]):
        return {'status': 'NOT_EXECUTED', 'scientific_execution': False,
                'reason': 'Missing observed execution/actual backend identity', 'declared': payload}
    if not device_probe.get('available', False):
        return {'status': 'BLOCKED', 'scientific_execution': False,
                'reason': 'Device preflight failed; no accepted science evidence'}
    src = payload.get('source_sha256')
    if not isinstance(src, str) or len(src) != 64 or any(x not in '0123456789abcdefABCDEF' for x in src):
        return {'status': 'UNQUALIFIED', 'scientific_execution': True,
                'reason': 'Missing valid source SHA-256 digest', 'declared': payload}
    # Report execution, not certified parity; science gate remains independently controlled.
    record = dict(payload)
    record['status'] = 'EXECUTED_UNQUALIFIED'
    record['scientific_execution'] = True
    record['science_gate_qualified'] = False
    if name == 'gpu':
        record['precision_warning'] = 'Arc A770 default FP32; scientific parity and convergence remain unverified.'
    return record


def _call_science_adapter(root: Path, cfg: dict, mode: str, out: Path, probes: dict) -> tuple[dict, str]:
    # A registered scientific adapter is a falsifier-specific extension point.
    # Only import explicit instance-root code; not a similarly named package from elsewhere.
    f = root/'experiment'/'backend_matrix.py'
    if not f.is_file():
        return {}, 'UNIMPLEMENTED: experiment/backend_matrix.py absent'
    import importlib.util
    spec = importlib.util.spec_from_file_location('_sst_instance_backend_matrix_v111', f)
    if spec is None or spec.loader is None:
        return {}, 'UNIMPLEMENTED: adapter cannot be loaded'
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        callback = getattr(module, 'run_backend_matrix', None)
        if not callable(callback):
            return {}, 'UNIMPLEMENTED: run_backend_matrix() missing'
        result = callback(root=root, cfg=cfg, mode=mode, output_dir=out/'backend_science', devices=probes)
        if not isinstance(result, dict):
            return {}, 'INVALID: adapter must return a dict keyed by py, cpp and gpu'
        return result, 'CALLED'
    except Exception as e:
        return {}, f'ERROR: {type(e).__name__}: {e}'


def run_auto_matrix(root: str | Path, cfg: dict, mode: str, out: str | Path,
                    backend_manifest: dict | None = None) -> dict:
    """Always do preflight in blind science runs; optional adapter runs science.

    Does not modify the caller's ledger, preregistration, or science equations.
    Existing falsifiers without an adapter remain executable but unqualified.
    """
    root, out = Path(root).resolve(), Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    policy = cfg.get('auto_backends', {}) or {}
    enabled = policy.get('enabled', True)
    if not enabled:
        result = {'schema': SCHEMA, 'mode': mode, 'status': 'DISABLED_EXPLICITLY', 'scientific_gate_qualified': False}
    else:
        devices = probe_all(root)
        science, called = _call_science_adapter(root, cfg, mode, out, devices)
        records = {k: _validate_record(k, science.get(k), devices[k]) for k in BACKENDS}
        all_devices = all(devices[k].get('available') for k in BACKENDS)
        all_science = all(records[k].get('scientific_execution') for k in BACKENDS)
        result = {'schema': SCHEMA, 'framework_version': '1.0.11', 'mode': mode,
                  'policy': {'auto_preflight': True,
                             'require_all_devices': bool(policy.get('require_all_devices', False)),
                             'require_all_science': bool(policy.get('require_all_science', False))},
                  'devices': devices, 'adapter_status': called,
                  'scientific': records, 'all_devices_available': all_devices,
                  'all_science_executed': all_science, 'scientific_gate_qualified': False,
                  'qualification': 'BACKEND_DIAGNOSTIC_ONLY',
                  'status': 'SCIENCE_EXECUTED_UNQUALIFIED' if all_science else 'INCOMPLETE',
                  'note': 'Backend availability and science parity are distinct. No gate PASS is generated automatically.'}
    dest = out/'AUTO_BACKEND_MATRIX.json'
    dest.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    if enabled and ((policy.get('require_all_devices', False) and not result['all_devices_available']) or
                    (policy.get('require_all_science', False) and not result['all_science_executed'])):
        raise RuntimeError('Strict auto-backend policy FAILED; see '+str(dest))
    return result
