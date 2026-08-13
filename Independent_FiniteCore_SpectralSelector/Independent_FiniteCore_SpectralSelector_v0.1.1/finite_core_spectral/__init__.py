"""Dimensionless finite-core spectral selector."""
from .core import independence_manifest, run_scan, spectrum_at_q, validate_config
from .convergence import adaptive_case, evaluate_gap_convergence, evaluate_primary_convergence
__all__=['independence_manifest','run_scan','spectrum_at_q','validate_config','adaptive_case','evaluate_gap_convergence','evaluate_primary_convergence']
