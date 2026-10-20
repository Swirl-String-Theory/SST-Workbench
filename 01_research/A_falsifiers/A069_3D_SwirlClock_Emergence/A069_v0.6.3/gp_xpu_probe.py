#!/usr/bin/env python3
"""A069 v0.6.3 DEVELOPMENT: strict-XPU 3D GP FFT and step screening.

No physics certification, no knot tracking, no 1.0.10 claim.  A checkpoint from
v0.6.2 can be used as input; all output paths are create-once.  The CPU-FP64
path is the numerical comparison authority for this screening experiment.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def synthetic_initial(n: int, box: float) -> np.ndarray:
    """Deliberately unknotted GP field, nontrivial in all three dimensions."""
    x = (np.arange(n, dtype=np.float64) - n // 2) * (box / n)
    z = (2 * np.pi / box) * x
    density = (1 + 0.035 * np.sin(z[:, None, None])
                + 0.019 * np.cos(2 * z[None, :, None])
                + 0.011 * np.sin(3 * z[None, None, :]))
    phase = (0.027 * np.sin(z[:, None, None] + 2 * z[None, :, None])
             + 0.021 * np.cos(z[None, None, :] - z[:, None, None]))
    return np.ascontiguousarray(density * np.exp(1j * phase), dtype=np.complex128)


def kinetic_numpy(n: int, box: float, dt_step: float) -> np.ndarray:
    k = 2 * np.pi * np.fft.fftfreq(n, box/n)
    k2 = k[:,None,None]**2+k[None,:,None]**2+k[None,None,:]**2
    return np.exp(-.5j * dt_step * k2)


def numpy_step(z: np.ndarray, kin: np.ndarray, dt_step: float, mu: float) -> np.ndarray:
    phase1 = np.exp(-.5j * dt_step * mu * (np.abs(z)**2-1))
    z = z * phase1
    z = np.fft.ifftn(np.fft.fftn(z) * kin)
    return z * np.exp(-.5j * dt_step * mu * (np.abs(z)**2-1))


def relative_l2(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm((a-b).ravel()) / max(np.linalg.norm(b.ravel()), 1e-30))


def select_torch_device(torch, kind: str, expected: str):
    if kind == 'cpu':
        return torch.device('cpu'), {'name':'CPU (developer smoke, not GPU proof)', 'xpu_used':False}
    if not hasattr(torch, 'xpu') or not torch.xpu.is_available():
        raise RuntimeError('NO_XPU: torch.xpu.is_available() is false. REFUSING SILENT CPU FALLBACK.')
    details = []
    for i in range(torch.xpu.device_count()):
        details.append((i, torch.xpu.get_device_name(i)))
    found = [(i,name) for i,name in details if expected.casefold() in name.casefold()]
    if not found:
        raise RuntimeError(f'EXPECTED_GPU_NOT_FOUND: expected {expected!r}; XPU devices: {details}')
    i, name = found[0]
    return torch.device(f'xpu:{i}'), {'name':name,'xpu_used':True,'xpu_index':i, 'all_xpu':details}


def sync(torch, device):
    if device.type == 'xpu':
        torch.xpu.synchronize(device)


def torch_k2(torch, n: int, box: float, device):
    k = torch.fft.fftfreq(n, d=box/n, device=device, dtype=torch.float32) * (2*math.pi)
    return k[:,None,None]**2+k[None,:,None]**2+k[None,None,:]**2


def torch_step(torch, z, kin, dt_step, mu):
    z = z * torch.exp((-0.5j*dt_step*mu) * (torch.abs(z)**2-1))
    spectral = torch.fft.fftn(z)
    z = torch.fft.ifftn(spectral * kin)
    return z * torch.exp((-0.5j*dt_step*mu) * (torch.abs(z)**2-1))


def checkpoint_state(p: Path):
    with np.load(p, allow_pickle=False) as f:
        keys = set(f.files)
        required = {'psi','dt','box','xi','mu','case','step','source_sha256','grid_n'}
        if not required <= keys:
            raise ValueError(f'checkpoint missing fields: {sorted(required-keys)}')
        state = np.asarray(f['psi'],dtype=np.complex128).copy()
        meta = {k: f[k].item() for k in ('dt','box','xi','mu','case','step','source_sha256','grid_n')}
    if state.shape != (int(meta['grid_n']),)*3:
        raise ValueError('invalid checkpoint: shape/grid mismatch')
    if not np.isfinite(state).all():
        raise ValueError('invalid checkpoint: NaNs/infinities')
    return state, meta


def audit(args):
    import torch
    dev, devmeta = select_torch_device(torch, args.device, args.expected_name)
    meta = {}
    if args.checkpoint:
        z, meta = checkpoint_state(args.checkpoint)
        n, box, dt_step, mu = len(z), float(meta['box']), float(meta['dt']),float(meta['mu'])
        if args.n is not None and args.n != n:
            raise ValueError('explicit n differs from checkpoint')
        origin = {'kind':'checkpoint','file':str(args.checkpoint.resolve()),'sha256':sha256(args.checkpoint),'meta':meta}
    else:
        n = args.n if args.n is not None else 32
        if n < 8 or n > 1024:
            raise ValueError('grid n outside development guard')
        box, dt_step, xi = args.box, args.dt, args.xi
        mu = 1/(2*xi*xi)
        z = synthetic_initial(n,box)
        origin = {'kind':'synthetic_bulk_control','no_knot':True}
    if n>128 and not args.allow_large:
        raise RuntimeError('LARGE_GRID_REQUIRES_EXPLICIT_FLAG: --allow-large')
    if args.steps < 1 or dt_step <= 0 or mu <= 0:
        raise ValueError('invalid steps/dt/mu')
    # Conservative, *screening-only* VRAM estimate, not a measured peak.
    # The 3-D transforms can allocate backend workspaces not visible from tensor sizes.
    vram_guard = {'estimate_bytes': int(1 * (2**30) + 200 * (n**3)),
                  'empirical_peak_calibrated': False}
    if dev.type == 'xpu':
        try:
            free_vram, total_vram = torch.xpu.mem_get_info(dev)
            vram_guard.update(free_bytes=int(free_vram), total_bytes=int(total_vram))
        except Exception as exc:
            raise RuntimeError(f'XPU_VRAM_QUERY_UNAVAILABLE: {exc}') from exc
        if free_vram < vram_guard['estimate_bytes']:
            raise RuntimeError(f'XPU_VRAM_GUARD: estimated {vram_guard["estimate_bytes"] / 2**30:.2f} GiB, free {free_vram / 2**30:.2f} GiB. No overcommit on this preflight.')
    start = time.perf_counter()
    z_gpu = torch.from_numpy(z.astype(np.complex64,copy=True)).to(dev)
    try:
        k2 = torch_k2(torch,n,box,dev)
        kin = torch.exp((-0.5j*dt_step) * k2)
        assert kin.device == z_gpu.device and z_gpu.dtype == torch.complex64
        check_fft = torch.fft.fftn(z_gpu)
        check_back = torch.fft.ifftn(check_fft)
        sync(torch,dev)
    except Exception as e:
        raise RuntimeError(f'XPU_3D_COMPLEX_FFT_FAILED: {type(e).__name__}: {e}') from e
    roundtrip = relative_l2(check_back.cpu().numpy().astype(np.complex128),z.astype(np.complex64).astype(np.complex128))
    np_fft = np.fft.fftn(z.astype(np.complex64).astype(np.complex128))
    fft_l2 = relative_l2(check_fft.cpu().numpy().astype(np.complex128),np_fft)
    sync(torch,dev)
    begin_gpu = time.perf_counter()
    for _ in range(args.steps):
        z_gpu = torch_step(torch,z_gpu,kin,dt_step,mu)
        if z_gpu.device != dev: raise RuntimeError('GPU_DEVICE_LOST: output moved to another device')
    sync(torch,dev)
    elapsed_gpu = time.perf_counter()-begin_gpu
    z_test = z_gpu.cpu().numpy()
    norm0 = np.sum(np.abs(z)**2,dtype=np.float64)
    norm_gpu = np.sum(np.abs(z_test)**2,dtype=np.float64)
    output={'schema':'A069-XPU-GP-PREFLIGHT-1','status':'DEVELOPMENT_NUMERIC_SCREENING_ONLY',
      'framework_target':'v1.0.10_LOCAL_VALIDATED_CANDIDATE_NOT_CANONICAL',
      'model':'3D GP with mu from v0.6.2; no Euler/clock certification',
      'source':origin,'device':str(dev),'device_info':devmeta,'torch_version':torch.__version__,
      'n':n,'box':box,'dt':dt_step,'mu':mu,'steps':args.steps,
      'state_dtype':'complex64','cpu_reference_dtype':'complex128','vram_guard':vram_guard,
      'fft_roundtrip_relative_l2':roundtrip,'fft_vs_numpy_fp64_relative_l2':fft_l2,
      'mass_drift_gpu_relative':float((norm_gpu-norm0)/norm0),
      'gp_gpu_time_seconds':elapsed_gpu,'setup_and_test_seconds':time.perf_counter()-start,
      'G32':'NOT_TESTED_BY_THIS_BACKEND_PROBE',
      'G34':'UNRESOLVED','G35':'UNRESOLVED',
      'claims':{'hardware_fft_supported':bool(devmeta['xpu_used']), 'GP_solver_parity':False,'trefoil_topology':False,'internal_clock':False}}
    if not args.no_cpu_reference:
        cpu_begin = time.perf_counter()
        kin_np = kinetic_numpy(n,box,dt_step)
        ref = z.copy()
        for _ in range(args.steps):
            ref = numpy_step(ref,kin_np,dt_step,mu)
        output['gp_cpu_fp64_time_seconds'] = time.perf_counter()-cpu_begin
        output['gp_gpu_vs_cpu_fp64_relative_l2'] = relative_l2(z_test.astype(np.complex128),ref)
        output['gp_gpu_vs_cpu_fp64_max_absolute'] = float(np.max(np.abs(z_test-ref)))
        output['pass_reference_screening'] = bool(
            output['gp_gpu_vs_cpu_fp64_relative_l2'] < args.tolerance
            and fft_l2 < args.tolerance
            and roundtrip < args.tolerance)
        output['claims']['GP_solver_parity'] = bool(output['pass_reference_screening'] and devmeta['xpu_used'])
    else:
        output['gp_cpu_fp64_time_seconds'] = None
        output['gp_gpu_vs_cpu_fp64_relative_l2'] = None
        output['pass_reference_screening'] = None
    if dev.type=='xpu':
        try:
            output['xpu_peak_allocated_bytes'] = int(torch.xpu.max_memory_allocated(dev))
            output['xpu_peak_reserved_bytes'] = int(torch.xpu.max_memory_reserved(dev))
        except Exception:
            output['xpu_memory_metrics']='not supported by this torch build'
    if not args.out:
        return output
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with open(args.out,'x',encoding='utf-8') as f:
        json.dump(output,f,indent=2,sort_keys=True,allow_nan=False,default=str)
        f.write('\n')
    return output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--device',choices=('xpu','cpu'),default='xpu')
    p.add_argument('--expected-name',default='A770',help='strict device name substring, refuses UHD fallback')
    p.add_argument('--n',type=int,default=None)
    p.add_argument('--box',type=float,default=10.)
    p.add_argument('--dt',type=float,default=.003)
    p.add_argument('--xi',type=float,default=.28)
    p.add_argument('--steps',type=int,default=8)
    p.add_argument('--checkpoint',type=Path,default=None)
    p.add_argument('--no-cpu-reference',action='store_true',help='throughput only; parity unresolved')
    p.add_argument('--allow-large',action='store_true',help='explicit for n>128; can exhaust VRAM')
    p.add_argument('--tolerance',type=float,default=2e-4,help='developer screening only; not physical threshold')
    p.add_argument('--out',type=Path,default=None)
    args=p.parse_args()
    try:
        result=audit(args)
    except Exception as exc:
        print(json.dumps({'status':'REJECTED_OR_UNSUPPORTED','error':str(exc),'no_gpu_claim':True},indent=2))
        return 2
    print(json.dumps(result,indent=2,sort_keys=True,default=str))
    return 0 if result.get('pass_reference_screening') is not False else 3

if __name__ == '__main__': raise SystemExit(main())
