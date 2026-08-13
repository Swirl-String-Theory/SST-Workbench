"""Build configuration for SST Kelvin/Floquet Workbench."""
from pathlib import Path
PACKAGE_NAME = "sst_kelvin_workbench"
EXT_BASENAME = "_native"
CPP_REL = Path("cpp") / "native.cpp"
STAMP_BASENAME = "native.stamp.json"
LOG_PREFIX = "[SST-KELVIN-NATIVE]"
