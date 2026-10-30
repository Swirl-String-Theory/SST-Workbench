"""Adversarial v0.2.9: geometry metadata, deposition, ridge and non-promotion."""
import json,sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from experiment.ruban import resolution_gate
from experiment.ruban_deposition import (initial_field,trilinear,track_field,
    run_deposition,package_outputs)
from experiment.ruban_study import run_ruban_study


def test_case_specific_geometry_metadata():
    r=resolution_gate(10,24,.5,.154)
    c=resolution_gate(10,24,.5,.32)
    assert r['rminor_cells']==pytest.approx(.154*24/10)
    assert c['rminor_cells']==pytest.approx(.32*24/10)
    assert c['sigma_over_rminor']==pytest.approx(1.5625)
    assert c['ruban_reference_parameters_apply_to_case'] is False
    assert c['delta_cells_IF_misinterpreted_as_Euler_sigma'] is None
    assert r['ruban_reference_parameters_apply_to_case'] is True


def test_periodic_trilinear_at_cell_centers():
    n=16;L=8
    a=np.arange(n**3*3,dtype=float).reshape(n,n,n,3)
    points=np.array([[.5*L/n-L/2,.5*L/n-L/2,.5*L/n-L/2],
        [(n-.5)*L/n-L/2]*3])
    assert np.array_equal(trilinear(a,points,L),np.array([a[0,0,0],a[-1,-1,-1]]))
    assert np.allclose(trilinear(a,points+L,L),trilinear(a,points,L))


def test_initial_field_uses_real_deposited_vorticity_and_no_physical_pass():
    a,sl,solver,uh,p=initial_field(ROOT,'ruban',16,10,.5,threads=1)
    b,_,_,_,_=initial_field(ROOT,'analytic_032',16,10,.5,threads=1)
    assert a['resolution']['geometry_B0']==.154 and b['resolution']['geometry_B0']==.32
    assert a['initial_energy_J_normalized']>0
    assert a['initial_enstrophy_m3_per_s2_normalized']>0
    assert 0<=a['spectral_enstrophy_fraction_near_dealias_boundary']<=1
    assert 0<=a['deposition_L2_smoothed_over_projected_squared']<=1+1e-12
    assert a['ridge_initial']['cross_section_overlap_risk']
    assert sl.shape==(16,16,3)
    assert not a['spatial_fidelity_qualified'] and not a['topology_certified']
    assert a['actual_euler_geometry_provenance'][0]['B0']==.154
    assert b['actual_euler_geometry_provenance'][0]['B0']==.32


def test_tracking_samples_actual_euler_field_without_claiming_topology():
    a,_,solver,uh,points=initial_field(ROOT,'ruban',16,10,.5,threads=1)
    t,arrays=track_field(solver,uh,points,T=.01,dt=.01,markers_count=32)
    assert t['steps']==1 and t['time_final']==pytest.approx(.01)
    assert arrays['markers'].shape==(2,32,3)
    assert arrays['ridge_proxy'].shape==(2,32,3)
    assert t['history'][-1]['marker_rigid_cyclic_rms']>=0
    assert not t['dynamic_topology_certified']
    assert t['material_markers_are_not_vortex_centerlines']


def test_scan_outputs_have_provenance_and_no_false_gate(tmp_path):
    out=tmp_path/'scan'
    r=run_deposition(ROOT,out,grids=(16,24),sigmas=(.5,),boxes=(10,),threads=1)
    assert r['cases']==4 and r['framework_gates']=='NOT_EXECUTED'
    assert len(r['grid_comparisons'])==2
    assert all(not x['spatial_convergence_certified'] for x in r['grid_comparisons'])
    assert (out/'INITIAL_FIELD_MATRIX.csv').exists()
    assert (out/'A075-v0.2.9_RUBAN_DEPOSITION_REPORT.pdf').is_file()
    assert len(list(out.glob('*_vorticity_xz_y0.npy')))==4
    assert all(x['physical_qualification'] is False for x in r['resolution_screening'])
    assert r['physical_answer']=='UNRESOLVED'
    p=package_outputs(tmp_path,out)
    assert Path(p['archive']).exists() and len(p['sha256'])==64


def test_existing_preview_now_uses_correct_case_metadata(tmp_path):
    out=run_ruban_study(ROOT,tmp_path,{'n':16,'n_up':24,'T':.02,'dt':.01,'threads':1,'core':.5})
    assert out['analytic_032_resolution']['rminor_cells']==pytest.approx(.32*16/10)
    c=json.loads((tmp_path/'analytic_032_base.json').read_text())
    assert c['config']['geometry']=='analytic_t23_B0_0p32'
    assert c['resolution']['geometry_B0']==.32
    r=json.loads((tmp_path/'ruban_base.json').read_text())
    assert r['config']['geometry']=='ruban_t23_B0_0p154'
    assert r['resolution']['geometry_B0']==.154


def test_reject_expensive_grid_without_explicit_consent(tmp_path):
    with pytest.raises(RuntimeError,match='GRID_BUDGET'):
        run_deposition(ROOT,tmp_path/'scan',grids=(136,),sigmas=(.5,),boxes=(10,),threads=1)
