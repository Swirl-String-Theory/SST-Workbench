"""Additive tests for A063 v0.1.1 analytical qualification."""
import json
import hashlib
from pathlib import Path
from hicks_hill import SphereVortex,root_families
from hicks_hill.qualification import boundary_ladder,interior_refinement,rational_torus_knot_candidate
from run_hicks import execute

ROOT=Path(__file__).resolve().parents[1]
POINTS=[(.23,.41),(.37,.21),(.52,-.3),(.49,.5),(.81,.12)]

def test_separate_family_fd_residuals():
    lam=root_families(1)
    fields={'Hill':SphereVortex(), 'Beltrami':SphereVortex(lam=lam['lambda1'][0]), 'ZeroTranslation':SphereVortex(lam=lam['lambda2'][0])}
    for name,field in fields.items():
        vals=interior_refinement(field,POINTS)
        assert len(vals)==4
        assert vals[-1]['max_euler_residual'] < vals[-2]['max_euler_residual']/2.5
        assert vals[-1]['max_abs_divergence']<2e-5
        assert vals[-1]['max_euler_residual']<2e-5
        if name=='Beltrami':assert vals[-1]['max_beltrami_residual']<2e-5
        if name=='ZeroTranslation':assert abs(field.U)<1e-10

def test_whole_surface_matching_ladders():
    for lam in [0,root_families(1)['lambda1'][0],root_families(1)['lambda2'][0]]:
        f=SphereVortex(lam=lam)
        r=boundary_ladder(f)
        assert r['velocity_converges'] and r['pressure_converges']
        assert all(x['n_theta']==121 for x in r['samples'])
        assert r['samples'][-1]['max_boundary_normal_velocity']<1e-10

def test_t34_numerical_closed_streamline_candidate():
    f=SphereVortex(lam=root_families(1)['lambda1'][0]);c=rational_torus_knot_candidate(f)
    assert c['classification_authority']=='CANDIDATE_ONLY'
    assert abs(c['winding_per_cycle']-.75)<1e-9
    assert abs(c['total_azimuthal_winding']-3)<1e-6
    assert abs(abs(c['total_poloidal_winding'])-4)<1e-6
    assert c['full_3d_closure_relative_a']<1e-6
    assert c['meridional_phase_monotone']
    assert c['no_finite_core_claim'] and c['no_independent_knot_invariant']

def test_release_seal_matches_sources():
    seal=json.loads((ROOT/'SOURCE_SEAL.json').read_text())
    assert seal['version']=='v0.1.1'
    for rel,hashval in seal['files'].items():
        assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==hashval

def test_end_to_end_ledger_summary_and_evidence(tmp_path):
    execute(tmp_path)
    ledger=json.loads((tmp_path/'GATE_LEDGER.json').read_text())
    summary=json.loads((tmp_path/'RUN_SUMMARY.json').read_text())
    controls=json.loads((tmp_path/'HICKS_CONTROLS.json').read_text())
    assert ledger['schema'].endswith('-2')
    r={x['gate_id']:x for x in ledger['records']}
    assert r['H3']['metrics']['max_euler'] < 1e-5
    assert r['H4']['metrics']['max_euler'] < 2e-5
    assert r['H7A']['status']=='PASS' and r['H7']['status']=='UNRESOLVED'
    assert r['H7B']['status']=='UNRESOLVED' and r['H8']['status']=='UNRESOLVED'
    assert summary['scientific_certification']=='NOT_RUN'
    assert ledger['ledger_sha256']==summary['gate_ledger_sha256']
    assert len(controls['interface_ladder'])==3
