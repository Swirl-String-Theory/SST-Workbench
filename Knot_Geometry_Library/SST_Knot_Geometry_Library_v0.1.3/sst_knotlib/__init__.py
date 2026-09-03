from .geometry import (
    TAU, classic_trefoil, torus_knot, shader_track_trefoil, figure8_s3,
    inverse_stereographic, stereographic_project, rotate_s3, s3_deform,
    resample_closed, curve_length, normalize_centerline, fourier_smooth,
    perturb_normal_modes,
)
from .frames import bishop_frame, thread_bundle, ribbon_edges
from .diagnostics import (
    curvature, min_nonlocal_distance, thickness_estimate, writhe, linking_number,
    convergence_report, qualify_seed, segment_stats, self_linking_report,
)
from .blind import make_blind_campaign, geometry_sha256, verify_blind_campaign

from .version import __version__

from .adapters import prepare_for_falsifier
