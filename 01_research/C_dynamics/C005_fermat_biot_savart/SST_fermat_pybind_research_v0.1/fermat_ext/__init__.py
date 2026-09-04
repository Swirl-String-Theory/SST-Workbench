"""Standalone SST Fermat research package; no SSTcore dependency."""

from .core import analyze_profile, sweep_profiles, write_csv, write_json
from .knot_scan import scan_torus_knot, torus_knot

__all__ = ["analyze_profile", "sweep_profiles", "scan_torus_knot", "torus_knot", "write_json", "write_csv"]
__version__ = "0.1.1"
