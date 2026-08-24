from __future__ import annotations
import importlib, platform, sys, json
from pathlib import Path

mods=["numpy","pybind11","setuptools"]
rows={}
ok=True
for m in mods:
    try:
        x=importlib.import_module(m)
        rows[m]=getattr(x,"__version__","available")
    except Exception as e:
        rows[m]=f"MISSING: {e}"
        ok=False

# Build-system regression guard: setuptools >=80 rejects ambiguous flat-layout
# discovery if the generated setup() does not explicitly declare packages.
_builder = Path(__file__).resolve().parent / "sst_thread_falsifier" / "native_ext" / "build_ext_if_needed.py"
_builder_text = _builder.read_text(encoding="utf-8")
_required = 'packages=["sst_thread_falsifier", "sst_thread_falsifier.native_ext"]'
_pyproject = Path(__file__).resolve().parent / "pyproject.toml"
_pyproject_text = _pyproject.read_text(encoding="utf-8")
_pyproject_required = 'packages = ["sst_thread_falsifier", "sst_thread_falsifier.native_ext"]'
_relative_cpp_required = '[r"{Path(CPP_REL).as_posix()}"]'
_short_temp_required = '"--build-temp", str(Path("build") / "temp_native")'
build_system_ok = (_required in _builder_text and _pyproject_required in _pyproject_text
                   and _relative_cpp_required in _builder_text
                   and _short_temp_required in _builder_text)
if not build_system_ok:
    ok=False
    rows["build_system"]=("FAIL: native builder must explicitly declare packages, "
                          "use relative cpp/native.cpp, and use short build/temp_native")
else:
    rows["build_system"]="explicit packages + short relative MSVC object path = PASS"

_root = Path(__file__).resolve().parent
_expected_obj = _root / "build" / "temp_native" / "cpp" / "native.obj"
_obj_chars = len(str(_expected_obj))
rows["native_object_path_guard"] = {
    "expected_object_path_chars": _obj_chars,
    "soft_limit": 240,
    "status": "PASS" if _obj_chars < 240 else "FAIL",
    "path": str(_expected_obj),
}
if _obj_chars >= 240:
    ok=False

print(json.dumps({"python":sys.version,"platform":platform.platform(),"dependencies":rows,"status":"PASS" if ok else "FAIL"},indent=2))
raise SystemExit(0 if ok else 1)
