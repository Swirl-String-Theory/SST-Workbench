from .version import __version__
from .geometry import (
    TAU, classic_trefoil, torus_knot, shader_track_trefoil, figure8_s3, lissajous_7_4,
    inverse_stereographic, stereographic_project, rotate_s3, s3_deform,
    resample_closed, curve_length, normalize_centerline, fourier_smooth, perturb_normal_modes,
)
from .frames import bishop_frame, thread_bundle, ribbon_edges
from .diagnostics import (
    curvature, min_nonlocal_distance, thickness_estimate, writhe, linking_number,
    convergence_report, qualify_seed, segment_stats, self_linking_report, linking_matrix,
)
from .braid import braid_closure, braid_closure_components, braid_permutation, permutation_cycles
from .registry import KAtlasSnapshot, normalize_knot_id, infer_knot_id_from_name
from .formats import load_geometry
from .providers import provider_status, certify_geometry, crosscheck_reference
from .topology import generate_topology_seed, braid_reference_report
from .records import make_knot_record
from .blind import make_blind_campaign, geometry_sha256, verify_blind_campaign
from .adapters import prepare_for_falsifier
from .policy import evaluate_record
from .library_root import find_knot_library_root, resolve_path_provenance, load_providers
from .inventory import inventory_sources, classify_legacy_path
from .dataset import scan_dataset
