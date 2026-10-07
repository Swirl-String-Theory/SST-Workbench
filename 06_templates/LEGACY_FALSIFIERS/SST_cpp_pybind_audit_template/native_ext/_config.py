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


def package_root() -> Path:
    """Project root (parent of the native_ext package folder)."""
    return Path(__file__).resolve().parent.parent


def default_output_dir() -> Path:
    """Inside-package outputs: ``{folder_name}_outputs``."""
    root = package_root()
    return root / f"{root.name}_outputs"
