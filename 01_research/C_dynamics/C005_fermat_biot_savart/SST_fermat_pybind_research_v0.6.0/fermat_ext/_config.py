"""Project and build configuration."""

from pathlib import Path

PACKAGE_NAME = "fermat_ext"
EXT_BASENAME = "_fermat_native"
CPP_DIR_REL = Path("cpp")
STAMP_BASENAME = "fermat_native.stamp.json"
LOG_PREFIX = "[sst-fermat]"
RESULT_SCHEMA = "sst.fermat.audit.v0.6.0"
