"""Build configuration for the SST counter-pulley falsifier."""
from pathlib import Path
PACKAGE_NAME = "sst_counterpulley"
EXT_BASENAME = "_native"
CPP_REL = Path("cpp") / "native.cpp"
STAMP_BASENAME = "native.stamp.json"
LOG_PREFIX = "[sst_counterpulley_native]"
