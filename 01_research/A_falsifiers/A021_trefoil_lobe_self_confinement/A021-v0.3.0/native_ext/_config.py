from pathlib import Path
PACKAGE_NAME = "native_ext"
EXT_BASENAME = "_native"
CPP_REL = Path("cpp") / "native.cpp"
PROBE_CPP_REL = Path("cpp") / "list_sycl_devices.cpp"
STAMP_BASENAME = "native.stamp.json"
LOG_PREFIX = "[SST-TREFOIL-NATIVE]"
