from __future__ import annotations
import importlib,sys,math
from pathlib import Path
import numpy as np
from .util import sha256_file

def import_c006(c006_root):
    root=Path(c006_root).resolve()
    if not (root/"sst_kelvin_workbench").is_dir():
        raise FileNotFoundError(f"C006 package missing under {root}")
    s=str(root)
    if s not in sys.path: sys.path.insert(0,s)
    return {
      "backend":importlib.import_module("sst_kelvin_workbench.backend"),
      "fallback":importlib.import_module("sst_kelvin_workbench.fallback"),
      "dynamics":importlib.import_module("sst_kelvin_workbench.dynamics"),
      "spectral":importlib.import_module("sst_kelvin_workbench.spectral_cert"),
      "orbit":importlib.import_module("sst_kelvin_workbench.orbit"),
      "monodromy":importlib.import_module("sst_kelvin_workbench.monodromy"),
    }

def native_preflight(c006_root, cfg):
    """Build/import C006 native backend and compare it against the Python reference kernel."""
    c006=import_c006(c006_root)
    native,name=c006["backend"].load_backend(
        force_python=False,
        skip_build=False,
        force_build=bool(cfg.get("force_rebuild",False)),
        build_verbose=True)
    if name!="cpp":
        raise RuntimeError(f"C006_NATIVE_REQUIRED: backend resolved to {name!r}, expected 'cpp'")
    fb=c006["fallback"]
    n=int(cfg.get("parity_points",16))
    t=np.linspace(0,2*math.pi,n,endpoint=False)
    # Non-degenerate deterministic closed curves.
    plus=np.column_stack((np.cos(t),np.sin(t),0.15*np.sin(2*t)))
    minus=np.column_stack((0.8*np.cos(t+0.23),0.8*np.sin(t+0.23),0.35+0.12*np.cos(3*t)))
    gp,gm,eps=1.0,-1.0,0.10
    if hasattr(native,"pair_rhs"):
        vn=np.asarray(native.pair_rhs(plus,minus,gp,gm,eps),float)
    else:
        vp=(np.asarray(native.induced_velocity(plus,plus,gp,eps),float)+
            np.asarray(native.induced_velocity(plus,minus,gm,eps),float))
        vm=(np.asarray(native.induced_velocity(minus,minus,gm,eps),float)+
            np.asarray(native.induced_velocity(minus,plus,gp,eps),float))
        vn=np.vstack((vp,vm))
    vp=np.asarray(fb.pair_rhs(plus,minus,gp,gm,eps),float)
    diff=vn-vp
    rel=float(np.linalg.norm(diff)/max(np.linalg.norm(vp),1e-30))
    max_abs=float(np.max(np.abs(diff)))
    rtol=float(cfg.get("parity_relative_l2_max",1e-10))
    atol=float(cfg.get("parity_max_abs_max",1e-11))
    if not (np.all(np.isfinite(vn)) and rel<=rtol and max_abs<=atol):
        raise RuntimeError(
            f"C006_NATIVE_PARITY_FAIL: relative_l2={rel:.6g} (max {rtol}), "
            f"max_abs={max_abs:.6g} (max {atol})")
    info={"status":"PASS","backend":"cpp","parity_points":n,
          "relative_l2":rel,"max_abs":max_abs,
          "relative_l2_max":rtol,"max_abs_max":atol}
    if hasattr(native,"backend_info"):
        try: info["native_backend_info"]=dict(native.backend_info())
        except Exception: pass
    return info

def provenance(c006_root):
    root=Path(c006_root).resolve(); files={}
    for rel in ["sst_kelvin_workbench/dynamics.py","sst_kelvin_workbench/backend.py",
                "sst_kelvin_workbench/fallback.py","sst_kelvin_workbench/build_ext_if_needed.py",
                "sst_kelvin_workbench/spectral_cert.py","sst_kelvin_workbench/orbit.py",
                "sst_kelvin_workbench/monodromy.py","SPECTRAL_THRESHOLDS_FROZEN.json","THRESHOLDS_FROZEN.json"]:
        p=root/rel
        if p.exists(): files[rel]={"path":str(p),"sha256":sha256_file(p)}
    return {"c006_root":str(root),"version":"0.3.0","files":files}
