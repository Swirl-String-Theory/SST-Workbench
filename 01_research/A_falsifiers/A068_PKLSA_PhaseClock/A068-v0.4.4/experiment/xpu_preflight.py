"""Read-only Intel Arc/XPU diagnostic: no pip edits, no implicit CPU fallback."""
from __future__ import annotations
import sys,platform

def inspect_xpu():
    info={'schema':'A068-XPU-PREFLIGHT-v0.4.4','python':sys.version.split()[0],
          'platform':platform.platform(),'requested_backend':'pytorch-xpu',
          'no_cpu_fallback':True,'environment_changes_performed':False}
    try:
        import torch
        info['torch_version']=torch.__version__
        info['torch_cuda_version']=getattr(torch.version,'cuda',None)
        info['torch_xpu_available']=bool(hasattr(torch,'xpu') and torch.xpu.is_available())
        if info['torch_xpu_available']:
            info['xpu_count']=torch.xpu.device_count()
            info['xpu_devices']=[]
            for i in range(info['xpu_count']):
                try: name=torch.xpu.get_device_name(i)
                except Exception as exc:name=f'UNAVAILABLE:{type(exc).__name__}'
                info['xpu_devices'].append({'index':i,'name':name})
            info['status']='XPU_AVAILABLE_PARITY_STILL_REQUIRED'
        else:
            info['xpu_count']=0;info['status']='UNAVAILABLE_NO_FALLBACK'
            info['diagnostic']='Torch wheel, Intel GPU runtime or device unavailable; check wheel, drivers and XPU support in this Python environment.'
    except Exception as exc:
        info['status']='UNAVAILABLE_NO_FALLBACK';info['error']=f'{type(exc).__name__}: {exc}'
    return info
