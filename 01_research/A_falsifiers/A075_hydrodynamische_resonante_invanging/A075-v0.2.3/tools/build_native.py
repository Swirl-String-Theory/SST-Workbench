"""Use the authentic v1.0.10 pybind11/OpenMP toolchain and its compiler fingerprint."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from framework_bootstrap import load_framework
load_framework()
from sst_falsifier.native_build import build_pybind
r=build_pybind(ROOT,source_rel='native/cpp/native.cpp',package_rel='native_ext',module_name='_sst_native',prefer_openmp=True)
print(json.dumps(r.to_dict(),indent=2))
raise SystemExit(0 if r.success else 2)
