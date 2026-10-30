from pathlib import Path
import importlib,sys,json,math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'overlay'))
from experiment.abc_logic import adjudicate,classify_hierarchy
from experiment.pklsa_coupling import velocity,relative_residual
import numpy as np

def test_hierarchy_fails_closed():
    assert classify_hierarchy(scales=[2.5,2.7],coupling_verified=False,topology_providers=2,spatial_converged=True,temporal_converged=True)=='UNRESOLVED'
    assert classify_hierarchy(scales=[2.5,2.7],coupling_verified=True,topology_providers=1,spatial_converged=True,temporal_converged=True)=='UNRESOLVED'
    assert classify_hierarchy(scales=[2.5,2.7],coupling_verified=True,topology_providers=2,spatial_converged=True,temporal_converged=False)=='UNRESOLVED'
    assert classify_hierarchy(scales=[2.5,2.7],coupling_verified=True,topology_providers=2,spatial_converged=True,temporal_converged=True)=='C_HIERARCHY_SUPPORTED'

def test_missing_evidence_is_not_a_support():
    s=adjudicate([])
    assert s['A']=='UNRESOLVED' and s['B']=='UNRESOLVED'
    assert s['n_promoted']==0

def test_geometry_rigid_fit():
    theta=np.arange(24)*2*math.pi/24
    p=np.c_[np.cos(theta),np.sin(theta),np.zeros_like(theta)]
    # Translational + angular rigid field should have ~0 residual.
    omega=np.array([0.,0.,.15]);v=np.cross(omega,p)+[.2,-.1,.3]
    r,_=relative_residual(p,v)
    assert r<1e-12
    z=velocity(p,.1)
    assert z.shape==p.shape and np.isfinite(z).all()

def test_science_preregistration_is_complete():
    p=ROOT/'overlay'/'science_contract.json';d=json.loads(p.read_text())
    assert all(x in d for x in ['equations','observables','steps','falsification_criteria'])
    assert len(d['equations'])>=5 and len(d['steps'])>=5
    tex=(ROOT/'overlay'/'report'/'FALSIFIER_REPORT.tex').read_text()
    assert tex.count('% SST-REPORT-SECTION:')==16
    assert 'REPLACE_BEFORE_FREEZE' not in tex


def test_two_component_static_coupling_nonzero():
    from experiment.pklsa_coupling import mutual_velocity
    t=np.linspace(0,2*np.pi,32,endpoint=False)
    ring1=np.column_stack((np.cos(t),np.sin(t),np.zeros(32)))
    ring2=ring1.copy();ring2[:,2]=2.0
    v=mutual_velocity(ring1,ring2,.1,batch=7)
    assert v.shape == ring1.shape
    assert np.isfinite(v).all()
    assert np.linalg.norm(v)>0
