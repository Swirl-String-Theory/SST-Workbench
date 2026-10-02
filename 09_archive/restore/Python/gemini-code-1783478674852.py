"""SST SSDL (Separatrix Surface-Density Lift) audit package.

Numerieke test-harnas voor de Route A (DtN Monopole Normalization) en 
Route B (Planck-Normal Mode Count) stellingen.
"""

from .core import run_ssdl_audit

__all__ = ["run_ssdl_audit"]
__version__ = "0.1.0-ssdl-audit"