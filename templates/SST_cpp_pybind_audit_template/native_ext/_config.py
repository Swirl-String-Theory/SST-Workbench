"""Project knobs — edit these when you copy the template."""

from pathlib import Path

# Python package folder name (this directory).
PACKAGE_NAME = "native_ext"

# pybind11 module basename -> native_ext/_native*.pyd / .so
EXT_BASENAME = "_native"

# C++ source relative to project root (parent of PACKAGE_NAME).
CPP_REL = Path("cpp") / "native.cpp"

# Stamp file under build/ (hash-based rebuild).
STAMP_BASENAME = "native.stamp.json"

# Log prefix for build messages.
LOG_PREFIX = "[native_ext]"
