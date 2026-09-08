"""Build configuration inherited from SST_cpp_pybind_audit_template."""
from pathlib import Path
PACKAGE_NAME = "native_ext"
EXT_BASENAME = "_native"
CPP_REL = Path("cpp") / "native.cpp"
STAMP_BASENAME = "sst6_native.stamp.json"
LOG_PREFIX = "[SST6-NATIVE]"
