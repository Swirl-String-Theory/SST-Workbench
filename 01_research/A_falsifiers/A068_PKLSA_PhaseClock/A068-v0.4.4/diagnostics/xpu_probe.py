"""Read-only Arc/XPU feature smoke. Never labels emulated double as native FP64.

Run inside a distinct venv prepared from official PyTorch XPU wheels.
"""
from __future__ import annotations
import json,platform,sys
from pathlib import Path

def probe():
    result={'schema':'A068-ARC-XPU-CAPABILITIES-v0.4.5','python':sys.version.split()[0],
            'platform':platform.platform(),'hardware_gpu_executed':False,
            'physical_fp64_claim':'FORBIDDEN_ON_ARC_A770',
            'requires_separate_cpu_fp64_reference':True}
    try:
        import torch
        result['torch']=torch.__version__
        if not hasattr(torch,'xpu') or not torch.xpu.is_available():
            result['status']='NO_XPU';return result
        names=[torch.xpu.get_device_name(i) for i in range(torch.xpu.device_count())]
        result['devices']=names
        result['selected_gpu']='xpu:0'
        try:
            a=torch.rand((3,8,8,8),device='xpu',dtype=torch.float32)
            fa=torch.fft.fftn(a,dim=(-3,-2,-1))
            back=torch.fft.ifftn(fa,dim=(-3,-2,-1)).real
            torch.xpu.synchronize()
            error=float(torch.linalg.vector_norm(back-a).to('cpu')/torch.linalg.vector_norm(a).to('cpu'))
            result['fp32_fft_roundtrip_relative_L2']=error
            result['fp32_fft_gpu_executed']=a.device.type=='xpu' and fa.device.type=='xpu'
        except Exception as exc:
            result['fp32_fft_error']=f'{type(exc).__name__}: {exc}';result['fp32_fft_gpu_executed']=False
        try:
            # Capability detection only. A working dtype is NOT native hardware FP64.
            d=torch.ones((4,),device='xpu',dtype=torch.float64)
            torch.xpu.synchronize()
            result['fp64_tensor_runtime_accepts_dtype']=d.device.type=='xpu'
        except Exception as exc:
            result['fp64_tensor_runtime_error']=f'{type(exc).__name__}: {exc}'
            result['fp64_tensor_runtime_accepts_dtype']=False
        result['hardware_gpu_executed']=bool(result.get('fp32_fft_gpu_executed',False))
        result['status']='FP32_FFT_READY' if result['hardware_gpu_executed'] else 'XPU_PRESENT_FFT_UNAVAILABLE'
    except Exception as exc:result['status']='IMPORT_OR_RUNTIME_FAILURE';result['error']=f'{type(exc).__name__}: {exc}'
    return result

if __name__=='__main__':
    out=probe()
    print(json.dumps(out,indent=2))
    Path('A068_XPU_HARDWARE_PREFLIGHT.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    raise SystemExit(0 if out.get('status')=='FP32_FFT_READY' else 2)
