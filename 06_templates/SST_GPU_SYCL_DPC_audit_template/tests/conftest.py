from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def native_mod():
    from native_ext.build_ext_if_needed import build_if_needed

    build_if_needed(force=False, verbose=False)
    try:
        from native_ext import _native

        return _native
    except Exception:
        return None
