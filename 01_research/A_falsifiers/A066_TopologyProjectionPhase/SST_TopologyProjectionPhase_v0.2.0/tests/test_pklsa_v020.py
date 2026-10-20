from pathlib import Path
from src.physics import static_geometry
ROOT=Path(__file__).resolve().parents[1]/'external_pklsa'/'reference'
def test_real_pklsa_n300_source_determinant_3():
 r=static_geometry(ROOT/'PKLSA_TREFOIL_3_1_N300_CENTERLINE.npz')
 assert r['point_count']==300
 assert r['knot_signature']['alexander_det_at_minus_one']==3
 assert r['status']=='STATIC_TOPOLOGY_DIAGNOSTIC'
def test_real_pklsa_surface_is_not_curve():
 r=static_geometry(ROOT/'PKLSA_3_1_CANDIDATE_SURFACE.npz')
 assert r['status']=='SURFACE_MESH_ONLY'
 assert r['euler_characteristic']==2
 assert r['genus_if_orientable_and_closed']==0
 assert r['G09_CENTERLINE_KNOT']=='UNRESOLVED_NO_CENTERLINE'
