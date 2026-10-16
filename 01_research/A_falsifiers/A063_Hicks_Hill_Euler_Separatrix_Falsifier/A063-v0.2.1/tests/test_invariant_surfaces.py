from __future__ import annotations
import json,math,sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from hicks_hill.analytic import SphereVortex,root_families
from invariant_surfaces import psi_peak,meridional_level,iso_embedding_certificate,surface_flux,winding_on_level
from run_invariant import verify_parent

@pytest.fixture(scope='module')
def ctx():
    f=SphereVortex(a=1.,rho=1.,A=1.,lam=root_families(1)['lambda1'][0])
    psi0=float(f.psi(.9683098301738062,0))
    lev=[meridional_level(f,psi0*m,ntheta=96) for m in (.9,1,1.1)]
    return f,psi0,lev

def test_parent_integrity():
    assert verify_parent()['gate_statuses']['T5']=='FAIL'

def test_preserves_parent_shear_fail():
    assert verify_parent()['gate_statuses']['T6']=='FAIL'

def test_imported_parent_stability_unresolved():
    assert verify_parent()['gate_statuses']['T8']=='UNRESOLVED'

def test_correct_beltrami_root(ctx):
    f,_,_=ctx
    assert abs(math.sin(f.lam)-f.lam*math.cos(f.lam))<1e-12

def test_level_root_target_reached(ctx):
    _,_,levels=ctx
    assert max(l['level_residual_max'] for l in levels)<1e-9

def test_levels_avoid_symmetry_axis(ctx):
    _,_,levels=ctx
    assert min(l['s_min'] for l in levels)>.02

def test_levels_stay_inside_sphere(ctx):
    _,_,levels=ctx
    assert min(l['sphere_clearance_min'] for l in levels)>.001

def test_star_shapes_radially_unique(ctx):
    _,_,levels=ctx
    assert all(l['radially_unique'] for l in levels)

def test_isotopy_to_planar_circle(ctx):
    _,_,levels=ctx
    assert all(iso_embedding_certificate(l)['valid_sampled_isotopy'] for l in levels)

def test_psi_surface_normal_flux(ctx):
    f,_,levels=ctx
    assert max(surface_flux(f,l,h=2e-4)['max_material_flux_relative'] for l in levels)<1e-7

def test_flux_quadratic_fd_convergence(ctx):
    f,_,levels=ctx;l=levels[1]
    a=surface_flux(f,l,h=2e-4)['max_material_flux_relative']
    b=surface_flux(f,l,h=1e-4)['max_material_flux_relative']
    assert a>b*3.4 and a<b*4.6

def test_psi_torus_rational_winding(ctx):
    f,_,levels=ctx
    assert abs(winding_on_level(f,levels[1])['W']-.75)<1e-6

def test_neighbor_level_nonconstant_winding(ctx):
    f,_,levels=ctx
    ws=[winding_on_level(f,l)['W'] for l in levels]
    assert ws[0]<.75<ws[2]

def test_axisymmetry_of_psi(ctx):
    f,_,levels=ctx;l=levels[1]
    assert np.max(np.abs(f.psi(l['s'],l['z'])-l['target']))<1e-9

def test_finite_differences_independent_cancellation(ctx):
    f,_,levels=ctx;l=levels[1]
    eps=1e-4
    s=float(l['s'][18]);z=float(l['z'][18]);us,up,uz=f.velocity(s,z)
    ds=(f.psi(s+eps,z)-f.psi(s-eps,z))/(2*eps)
    dz=(f.psi(s,z+eps)-f.psi(s,z-eps))/(2*eps)
    assert abs(us*ds+uz*dz)<1e-6

def test_expected_topological_core_is_unknotted(ctx):
    _,_,levels=ctx
    assert iso_embedding_certificate(levels[1])['core_curve'].endswith('planar unknot')

def test_serialized_report_data_when_available():
    p=ROOT/'A063_Hicks_Invariant_Surface_v0.2.1-outputs/GATE_LEDGER.json'
    if not p.exists():pytest.skip('FULL not run yet')
    data=json.loads(p.read_text())
    assert data['counts']['FAIL']==2
    assert {g['gate_id']:g['status'] for g in data['records']}['S6']=='FAIL'
