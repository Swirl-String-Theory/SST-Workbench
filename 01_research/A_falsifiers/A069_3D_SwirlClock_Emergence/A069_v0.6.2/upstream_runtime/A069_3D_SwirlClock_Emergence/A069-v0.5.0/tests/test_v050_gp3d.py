"""v0.5.0 pre-registered 3D knot initial-value and mode control tests."""
import json,hashlib
import numpy as np
import pytest
from pathlib import Path
from experiment.knotted_gp3d import (initialize,plaquette_vortices,simulate,bogoliubov_bulk_control,
                                     tangent_validation,candidate_frequency,mesh)
R=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('kind',['A','B'])
def test_periodic_winding_from_spanning_surface(kind):
    psi,meta=initialize(kind,n=24,xi=.5,segments=80)
    assert meta['periodic_face_gap']<1e-12
    assert meta['core_cells']>1
    wr=plaquette_vortices(psi)
    assert sum(v['count'] for v in wr.values())>20
    assert all(v['signed_sum']==0 for v in wr.values())

@pytest.mark.parametrize('kind',['A','B'])
def test_mirror_phase_parity(kind):
    p,_=initialize(kind,False,n=24,xi=.5,segments=80)
    q,_=initialize(kind,True,n=24,xi=.5,segments=80)
    n=len(p)
    parity=np.take(p,(-np.arange(n))%n,axis=0)
    # exact complex conjugation of phase under reflection for same curve orientation
    assert np.max(abs(q-np.conj(parity)))<3e-2

@pytest.mark.parametrize('kind',['A','B'])
def test_real_3d_short_dynamics(kind):
    r=simulate(kind,n=24,steps=18,xi=.5,segments=80,diag_every=3)
    assert r['max_mass_drift']<1e-9
    assert r['max_energy_drift']<1e-3
    assert r['knotted_initial_field']
    assert r['classification']=='REAL_3D_GP_KNOT_INITIAL_VALUE_EVOLUTION_SIMULATION_ONLY'
    assert not r['physical_clock_claim']

def test_bulk_bdg_mode_uses_many_data_cycles():
    a=bogoliubov_bulk_control(steps=1500,dt=.01)
    assert a['status']=='PASS'
    assert a['observed_cycles']>4
    assert a['fit_is_independent_of_analytic_target']
    assert a['relative_error']<.01

def test_bdg_tangent_is_independent():
    a=tangent_validation()
    assert a['status']=='PASS'
    assert a['relative_linearization_error']<1e-4

def test_knot_frequency_fail_closed_for_few_cycles():
    a=simulate('A',n=24,steps=48,xi=.5,segments=80,diag_every=2)
    b=candidate_frequency(a['trace'])
    assert b['status']=='UNRESOLVED'
    assert b['frequency'] is None

def test_config_is_pinned_and_references_are_only_sources():
    c=json.loads((R/'configs/GP3D_CAMPAIGN_V050.json').read_text())
    spec=json.loads((R/'science_contract.json').read_text())
    assert hashlib.sha256((R/'configs/GP3D_CAMPAIGN_V050.json').read_bytes()).hexdigest()==spec['gp3d_campaign_sha256']
    assert len(c['cases'])==6
    assert sorted({v['n'] for v in c['cases']})==[48,64]
    for illegal in ('golden','lorentz','compton','target_frequency'):
        assert illegal not in json.dumps(c).lower()
