from __future__ import annotations
import json, platform, sys
import numpy, scipy, pybind11, setuptools
from sst_kelvin_workbench.backend import load_backend, backend_info
m,name=load_backend(force_build=False,build_verbose=True)
out={"python":sys.version,"platform":platform.platform(),"numpy":numpy.__version__,"scipy":scipy.__version__,"pybind11":pybind11.__version__,"setuptools":setuptools.__version__,"backend":backend_info(skip_build=True)}
print(json.dumps(out,indent=2)); raise SystemExit(0 if name=='cpp' else 2)
