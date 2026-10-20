"""All checks are local method/integration controls, NOT physical certification."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
import numpy as np
import pytest
from experiment import dynamics, pipeline
from experiment.euler3d import Euler3D,load_geometry,normalized_components
from experiment.phaseclock import demo,extract_shape_invariants,compare_two

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/knot_3.1.txt'

def test_source_contract_hashes_match():
    a=pipeline.source_audit(ROOT)
    assert a['valid'] and len(a['files'])==50

def test_exact_native_provider_identity():
    assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='98a628af4ba5d09274f0a1845c351a7a3d633a39ff833a3ae0b78e351bafdabf'

def test_upstream_code_is_byte_identical():
    assert (ROOT/'data/A064_euler_tangent_upstream.py').read_bytes()==(ROOT/'experiment/euler3d.py').read_bytes()

def test_no_pretend_independent_pklsa_provider():
    c=json.loads((ROOT/'source_contract.json').read_text())
    assert not any(s['evidence_class']=='experimental' for s in c['sources'])
    assert len({s['provenance_family'] for s in c['sources']})==2
    assert c['replication_policy']['independent_physical_provider_count']==0

def test_method_positive_and_null_regressions():
    assert pipeline.controls(ROOT)['valid']
    x=demo()
    assert x['positive_two_shape_signals']['G3_phase_reproducibility']=='PASS_NUMERICAL_ONLY'
    assert x['negative_beating']['G3_phase_reproducibility']=='SCREEN_FAIL'
    assert x['negative_rigid_rotation_shape_invariants']['q1']['status']=='NO_CLOCK'

def test_original_curve_does_not_enter_as_time_series():
    c,_=load_geometry(SRC)
    assert len(c)==1 and c[0].shape==(47,3)

def test_solver_divergence_and_real_evolution():
    c,_=load_geometry(SRC)
    g=Euler3D(12,.4);u=g.velocity_from_curve(normalized_components(c)[0]);d=np.empty((0,3,12,12,12))
    v,_=g.rk4(u,d,.04)
    assert g.divergence_relative(v)<1e-10
    assert np.linalg.norm(v-u)>1e-7

def test_physics_source_is_not_si_calibrated():
    j=json.loads((ROOT/'data/EULER_SOURCE_AUDIT.json').read_text())
    assert j['model']=='geometry_initialized_periodic_3d_euler_model'
    assert j['material_transport_assessment']=='PERMEABLE_NONMATERIAL_FEATURE'

def test_reveal_is_intentionally_fail_closed():
    p=json.loads((ROOT/'blind_policy.json').read_text())
    assert p['reveal_requires_gate']=='G8'
    assert p['block_reveal_on_unresolved'] is True

def test_uniform_real_three_dimensional_snapshots():
    j,arr,*_=dynamics.simulation(SRC,n=12,T=2.,dt=.04,snapshots=51)
    assert arr['u'].shape==(51,12,12,12,3)
    assert np.allclose(np.diff(arr['t']),.04)
    assert np.max(abs(arr['u'][0]-arr['u'][-1]))>1e-4
    assert j['conservation_screen_pass']
    assert j['physical_clock']=='UNRESOLVED'

def test_hilbert_short_series_is_not_clock_evidence():
    a,arr,*_=dynamics.simulation(SRC,n=12,T=2.,dt=.04,snapshots=51)
    assert a['shape_q1_clock']['status']=='INDETERMINATE'
    assert a['enstrophy_clock']['status']=='INDETERMINATE'

def test_vorticity_shape_is_invariant_under_grid_translation():
    j,arr,*_=dynamics.simulation(SRC,n=12,T=2.,dt=.04,snapshots=51)
    x,y,diag=extract_shape_invariants(arr['u'],float(arr['domain_length']))
    rolled=np.roll(arr['u'],3,axis=1)
    xx,yy,_=extract_shape_invariants(rolled,float(arr['domain_length']))
    assert np.max(abs(x-xx))<1e-10
    assert np.max(abs(y-yy))<1e-10

def test_q_shape_q_enstrophy_distinct_functionals():
    j,arr,*_=dynamics.simulation(SRC,n=12,T=2.,dt=.04,snapshots=51)
    assert np.ptp(arr['q_shape'])>1e-9
    assert np.ptp(arr['q_enstrophy'])>1e-9
    assert not np.allclose(arr['q_shape'],arr['q_enstrophy'])

def test_invalid_core_or_time_rejected():
    with pytest.raises(ValueError):dynamics.simulation(SRC,n=12,dt=.03,T=2.)

def test_fully_preregistered_science_equation_ids():
    sci=json.loads((ROOT/'science_contract.json').read_text());ids={e['id'] for e in sci['equations']}
    assert {'E1','E2','E3','E4','E5','E6','E7'}<=ids
    assert all(set(step['formula_refs'])<=ids for step in sci['steps'])

def test_full_development_refinement_evidence_is_nonconvergent_when_supplied():
    development=ROOT/'data/FULL_LOCAL_DEVELOPMENT_RESULT.json'
    result=json.loads(development.read_text())
    assert result['convergence']['temporal_gate'] is True
    assert result['convergence']['spatial_gate'] is False
    assert result['convergence']['finite_core_robust_gate'] is False
    assert result['scientific_qualification']['physical_clock']=='UNRESOLVED'


def test_pipeline_records_g3_unresolved_after_running_basic(tmp_path):
    import shutil
    from types import SimpleNamespace
    from experiment.a004_adapter import library_root, workbench_from_instance, LIBRARY_RELATIVE
    wb=tmp_path/"SST-Workbench"
    r=wb/"01_research/A_falsifiers/A068_PKLSA_PhaseClock/A068-v0.4.2"
    shutil.copytree(library_root(workbench_from_instance(ROOT)), wb/LIBRARY_RELATIVE)
    shutil.copytree(ROOT/"data",r/"data")
    (r/"experiment").mkdir()
    for name in ('euler3d.py','historical.py','a004_adapter.py'):
        shutil.copy2(ROOT/'experiment'/name,r/'experiment'/name)
    shutil.copy2(ROOT/'source_contract.json',r/'source_contract.json')
    class Ledger:
        def __init__(self):
            self.rows={}
            self.defs={k:SimpleNamespace(enabled=True) for k in [f"G{i}" for i in range(10)]}
        def record(self,k,status,**kwargs):self.rows[k]=status
        def status(self,k):return self.rows.get(k)
        def skip_due_prerequisite(self,k,reason=""):self.rows[k]="NOT_RUN_PREREQUISITE"
    led=Ledger()
    manifest=pipeline.run_scientific_pipeline(r,{},led,"BASIC")
    assert [led.rows[k] for k in ("G0","G1","G2","G3","G4","G8")]==["PASS","PASS","PASS","UNRESOLVED","NOT_RUN_PREREQUISITE","NOT_RUN_PREREQUISITE"]
    assert manifest["actual_backend"]=="python-numpy-fp64"
    assert (r/"PKLSA_PhaseClock_v0.4.2-outputs"/"EULER_3D_FIELDS_MODEL_ONLY.npz").is_file()
    assert (r/"PKLSA_PhaseClock_v0.4.2-outputs"/"EULER_DYNAMICS_RESULTS.json").is_file()
    assert (r/"PKLSA_PhaseClock_v0.4.2-outputs"/"HISTORICAL_2015_EULER_MODEL_DIAGNOSTICS.json").is_file()
