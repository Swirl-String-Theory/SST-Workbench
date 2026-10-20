"""v0.4.4 regression: bounded numerical screens, never physical qualification."""
import json
from pathlib import Path
import numpy as np
from experiment.long_material import long_material_campaign,surface_quality_screen
from experiment.vortex_line_search import closure_search
from experiment.xpu_preflight import inspect_xpu
from experiment.material import create_torus
from experiment.euler3d import load_geometry
from experiment.pipeline import source_audit
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/knot_3.1.txt'

def test_long_run_synchronized_real_euler():
    a=long_material_campaign(SRC,n=8,T=.08,dt=.04,output_every=1,quality_probes=8)
    assert a['T_reached']==.08
    assert a['sampled_snapshots']==3
    assert len(a['max_volume_drifts'])==3
    assert a['history'][0]['detF_max_abs_error']<1e-12
    assert a['surface_embeddedness_certified'] is False
    assert a['vortex_tube_qualified'] is False

def test_long_horizon_sparse_samples_never_certified():
    a=long_material_campaign(SRC,n=8,T=.08,dt=.04,output_every=2,quality_probes=5)
    assert a['not_continuously_monitored']
    assert a['sampled_snapshots']==2
    assert a['T_requested']==.08
    assert a['history'][-1]['finest_mesh_quality']['surface_embeddedness'].startswith('UNRESOLVED')

def test_collision_screen_non_exhaustive_and_degenerate():
    c,_=load_geometry(SRC)
    s,_=create_torus(c,sections=16,sides=6)
    q=surface_quality_screen(s,probes=4)
    assert q['sampled_triangle_count']==4
    assert q['surface_embeddedness']=='UNRESOLVED_NOT_EXHAUSTIVE_OR_EXACT'
    s[:]=s[0,0]
    q=surface_quality_screen(s,probes=4)
    assert q['degenerate_triangle_count']>0

def test_return_map_finite_not_physical():
    d=closure_search(SRC,n=8,anchor_indices=(0,),lengths=(2.,),steps=8)
    assert len(d['trials'])==1 and d['best']['closure_distance']>0
    assert d['vortex_tube_qualified'] is False
    assert d['independent_source_count']==0

def test_xpu_preflight_never_claims_gpu_without_device():
    p=inspect_xpu()
    assert p['no_cpu_fallback']
    assert p['environment_changes_performed'] is False
    if not p.get('torch_xpu_available'):
        assert p['status']=='UNAVAILABLE_NO_FALLBACK'

def test_registered_full_long_t_and_code_hash():
    c=json.loads((ROOT/'data/V044_REGISTERED_MATRIX.json').read_text())
    assert c['long_horizon_mesh']['FULL']['T']==20.
    assert c['long_horizon_mesh']['CERTIFY']['T']==20.
    assert c['gpu_parity_by_mode']['CERTIFY']['steps']>=500
    s=source_audit(ROOT)
    assert s['valid'],[k for k,v in s['files'].items() if not v['match']]
    assert all(k in s['files'] for k in ('experiment/long_material.py','experiment/vortex_line_search.py','experiment/xpu_preflight.py'))
