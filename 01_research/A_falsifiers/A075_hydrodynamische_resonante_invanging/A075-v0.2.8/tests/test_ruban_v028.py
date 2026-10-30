"""Ruban 2018 exact-seed adversarial diagnostics. No physics certification."""
from pathlib import Path
from dataclasses import replace
import hashlib,json,sys
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from experiment.ruban import (PRIMARY,B0,DELTA,LAMBDA,verify_geometry,load_primary_seed,
                              analytic_torus,resolution_gate)
from experiment.euler3d import Config,Euler3D
from experiment.ruban_study import evolve_one,run_ruban_study

def primary():return ROOT/'inputs/ruban_t23'/PRIMARY

def test_exact_ruban_parameters_and_windings():
    assert B0==77/500 and DELTA==1/20
    assert np.isclose(LAMBDA,4.049158683274018)
    g=verify_geometry(primary())
    assert g['geometric_fidelity_pass'] and g['points']==2048
    assert g['toroidal_winding']==2 and g['poloidal_winding']==3
    assert g['max_r0_residual']<1e-12
    assert not g['author_perturbation_reconstructed']

def test_seed_bytes_cannot_change_silently(tmp_path):
    dst=tmp_path/PRIMARY
    dst.write_bytes(primary().read_bytes())
    (tmp_path/'SEED_MANIFEST.json').write_bytes((primary().parent/'SEED_MANIFEST.json').read_bytes())
    a=dst.read_bytes();dst.write_bytes(a.replace(b'0',b'1',1))
    with pytest.raises(ValueError,match='SHA256'):load_primary_seed(dst)

def test_ruban_does_not_accidentally_copy_legacy_b0_geometry():
    xyz,meta=load_primary_seed(primary())
    b=analytic_torus(.32,n=2048)
    assert len(xyz)==len(b)
    assert abs(np.mean(np.hypot(np.hypot(xyz[:,0],xyz[:,1])-1,xyz[:,2]))-.154)<1e-12
    assert abs(np.mean(np.hypot(np.hypot(b[:,0],b[:,1])-1,b[:,2]))-.32)<1e-12
    assert meta['source']=='RUBAN_ANALYTIC_RECONSTRUCTION'
    assert meta['delta_regulator']==.05

def test_actual_field_initializer_is_only_one_curve_and_reproducible():
    c=Config(n=16,box=10,core=.5,dt=.01,final_time=.02,
          incoming=False,receiver_on=True,initial_condition='ruban_isolated',
          ruban_seed_path=str(primary()))
    solver=Euler3D(c);a,prov=solver.initial_velocity()
    b,_=solver.initial_velocity()
    assert len(prov)==1 and prov[0]['B0']==.154
    assert np.array_equal(a,b) and np.linalg.norm(a)>0
    c2=replace(c,initial_condition='legacy_t23_isolated')
    z,pr=Euler3D(c2).initial_velocity()
    assert len(pr)==1 and pr[0]['B0']==.32
    assert not np.array_equal(a,z)

def test_Ruban_Euler_screen_is_no_topological_certification():
    c=Config(n=16,box=10,core=.5,dt=.01,final_time=.02,
          incoming=False,initial_condition='ruban_isolated',ruban_seed_path=str(primary()))
    r=evolve_one(c)
    assert r['steps']==2 and r['physical_final_time_reached']
    assert r['physical_stability']=='UNRESOLVED' and not r['topology_conserved_certified']
    assert np.isfinite(r['spectrum_difference_final'])

def test_optional_refinement_separate_and_no_fake_free_space(tmp_path):
    opts={'n':16,'n_up':24,'T':.02,'dt':.01,'threads':1,'core':.5,
          'ruban_refinement':True,'backend':'cpu-scipy-fft'}
    s=run_ruban_study(ROOT,tmp_path,opts)
    assert len(s['levels'])==6 and s['refinement_executed']
    assert s['geometry']['geometric_fidelity_pass']
    assert s['periodic_images_present'] and not s['stability_certified']
    assert s['physical_answer']=='UNRESOLVED'
    assert s['ruban_resolution']['rminor_cells']==.154/(10/16)
    assert (tmp_path/'ruban_dt_half.json').is_file()

def test_default_mode_preserves_prior_a075():
    from experiment.science import _resolve
    p=_resolve('BASIC',{'threads':12})
    assert not p['ruban_study'] and not p['ruban_refinement']
    assert p['knots']==['0_1','3_1','5_2','6_1']

def test_framework_seed_source_and_gate_plans():
    from framework_bootstrap import load_framework
    load_framework()
    from sst_falsifier.gates import validate_gate_plan
    from experiment.qualification import inspect_sources
    g={x['gate_id']:x for x in json.loads((ROOT/'gate_plan.json').read_text())['gates']}
    assert g['G11']['requires']==['G1'] and g['G12']['requires']==['G11']
    assert validate_gate_plan(ROOT/'gate_plan.json')==[]
    src=inspect_sources(ROOT)
    assert src['passed'] and len(src['sources'])==6
    assert all(x['hash_match'] for x in src['sources'])
    assert not resolution_gate(10,80,.5)['spatial_fidelity_qualified']
