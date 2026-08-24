"""Ensure matrix directory is on sys.path for convert_catalog_kpc imports."""

from __future__ import annotations

import sys
from pathlib import Path

_MATRIX_DIR = Path(__file__).resolve().parents[1]
if str(_MATRIX_DIR) not in sys.path:
    sys.path.insert(0, str(_MATRIX_DIR))
