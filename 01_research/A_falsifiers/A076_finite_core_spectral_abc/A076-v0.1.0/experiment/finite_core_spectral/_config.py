"""Build/runtime configuration for the dimensionless spectral selector."""
from pathlib import Path
PACKAGE_NAME = "finite_core_spectral"
EXT_BASENAME = "_native"
CPP_REL = Path("cpp") / "native.cpp"
STAMP_BASENAME = "finite_core_spectral_native.stamp.json"
LOG_PREFIX = "[finite-core-spectral]"
