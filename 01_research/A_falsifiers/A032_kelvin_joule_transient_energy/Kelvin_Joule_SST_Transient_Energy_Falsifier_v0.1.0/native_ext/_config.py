"""Build configuration for Kelvin-Joule SST GPU/SYCL native kernels."""
from pathlib import Path
PACKAGE_NAME = "native_ext"
EXT_BASENAME = "_native"
CPP_REL = Path("cpp") / "native.cpp"
PROBE_CPP_REL = Path("cpp") / "list_sycl_devices.cpp"
STAMP_BASENAME = "native.stamp.json"
LOG_PREFIX = "[KJ-SST-GPU]"
