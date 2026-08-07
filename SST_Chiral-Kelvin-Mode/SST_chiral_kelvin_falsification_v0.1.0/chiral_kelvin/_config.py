"""Configuration for SST chiral Kelvin falsification pack v0.1.0."""

from pathlib import Path

PACKAGE_NAME = "chiral_kelvin"
EXT_BASENAME = "_native"

CPP_REL = Path("cpp") / "native.cpp"
STAMP_BASENAME = "native.stamp.json"
LOG_PREFIX = "[sst_chiral_kelvin]"

# ---------------------------------------------------------------------------
# SST canonical constants
# ---------------------------------------------------------------------------

V_SWIRL = 1.09384563e6       # m s^-1
R_C = 1.40897017e-15        # m
RHO_CORE = 3.8934358266918687e18  # kg m^-3
RHO_F = 7.0e-7              # kg m^-3

F_SWIRL_MAX = 29.053507     # N
F_GR_MAX = 3.02563e43       # N

PI = 3.141592653589793238462643383279502884

# Canonical circulation magnitude:
#
# Gamma_0 = 2 pi r_c |v_swirl|
#
GAMMA_0 = 2.0 * PI * R_C * V_SWIRL

# ---------------------------------------------------------------------------
# Numerical defaults
# ---------------------------------------------------------------------------

DEFAULT_N = 32

# The regularization length 'a' is deliberately explicit.
# v0.1.0 defaults to a = r_c, but this is swept as a falsification parameter.
DEFAULT_CORE_A = R_C

# Baseline ring geometry
DEFAULT_RING_RADIUS = 20.0 * R_C

# Exploratory torus-trefoil geometry.
DEFAULT_TREFOIL_MAJOR_RADIUS = 6.0 * R_C
DEFAULT_TREFOIL_MINOR_RADIUS = 2.0 * R_C

DEFAULT_REL_TOL = 1.0e-9
