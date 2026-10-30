"""Bounded A011 geometry and native parity check without auto-building source."""
import importlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
base = ROOT / '01_research/A_falsifiers/A011_maxwell_1_kinetic_energy/A011-v0.3.1'
sys.path.insert(0, str(base / 'src'))
import pytest
from maxwell_sst_falsifier.native_ext import core

# Import the existing ABI-compatible module directly; never call the package's
# auto-builder, which could change historical build products in place.
native = importlib.import_module('maxwell_sst_falsifier.native_ext._native')
core._BACKEND, core._BACKEND_NAME = native, 'cpp'
print(json.dumps({'python': sys.version, 'native_binary': native.__file__, 'backend': core.backend_info(), 'automatic_build_disabled': True}), flush=True)
raise SystemExit(pytest.main(['-p', 'no:cacheprovider', '-q', '-rA',
                             str(base / 'tests/test_geometry_v02.py'),
                             str(base / 'tests/test_native_parity_v02.py')]))
