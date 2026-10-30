from __future__ import annotations
import os, platform, sys, subprocess
from pathlib import Path
from typing import Any
from .util import write_json


def _version(cmd):
    try:
        cp=subprocess.run(cmd,text=True,capture_output=True,timeout=5)
        s=(cp.stdout or cp.stderr).strip().splitlines()
        return s[0] if s else None
    except Exception: return None


def environment_record() -> dict[str,Any]:
    return {
        "schema":"SST-ENVIRONMENT-2",
        "python":sys.version,
        "python_cache_tag":getattr(sys.implementation,"cache_tag",None),
        "executable":sys.executable,
        "platform":platform.platform(),
        "machine":platform.machine(),
        "processor":platform.processor(),
        "cwd":os.getcwd(),
        "env":{k:os.environ.get(k) for k in (
            "OMP_NUM_THREADS","SST_BACKEND","SST_SYCL_ALLOW_FP32","SST_DISABLE_OPENMP",
            "ONEAPI_DEVICE_SELECTOR","SYCL_CACHE_PERSISTENT"
        )},
        "compilers":{
            "cxx":_version([os.environ.get("CXX","c++"),"--version"]),
            "icpx":_version([os.environ.get("ICPX","icpx"),"--version"]),
        }
    }


def write_environment(path):
    d=environment_record(); write_json(path,d); return d
