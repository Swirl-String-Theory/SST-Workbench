"""Project knobs for the SST dark-knot Rayleigh audit harness."""

from pathlib import Path

PACKAGE_NAME = "sst_dark_knot_harness"
EXT_BASENAME = "_native"
CPP_REL = Path("cpp") / "native.cpp"
STAMP_BASENAME = "dark_knot_native.stamp.json"
LOG_PREFIX = "[sst-dark-knot]"
