"""A062-v0.5.0 gates. Unit-tests do not assert long-term stability or gravity."""
from pathlib import Path
import hashlib,json
import numpy as np
from microgravity.geometry import providers
from microgravity.spectral_dynamics_v050 import SpectralBox, test_abc_decay as abc_reference, integrate_e011, periodic_stress_monopole
from microgravity.dynamic_campaign_v050 import run_dynamic
ROOT=Path(__file__).resolve().parents[1]

def test_e011_provenance():
    pins=json.loads((ROOT/'inputs/e011/provider_pins.json').read_text())
    for entry in pins['provider_anchors']:
        assert hashlib.sha256((ROOT/entry['file']).read_bytes()).hexdigest()==entry['raw_sha256']

def test_abc_beltrami_analytic_decay():
    assert abc_reference()['relative_velocity_error']<1e-10

def test_euler_kinetic_energy_helicity_divergence():
    x=providers(96)['gilbert']['x']
    q=integrate_e011(x,24,0,T=.012,dt=.001)
    assert abs(q['energy_relative_drift'])<5e-4
    assert abs(q['last']['helicity']-q['initial']['helicity'])/max(abs(q['initial']['helicity']),1e-10)<1e-3
    assert q['div_relative_max']<1e-10

def test_navier_stokes_dissipation_budget():
    x=providers(96)['knotplot']['x']
    q=integrate_e011(x,24,.005,T=.012,dt=.001)
    assert q['last']['E']<q['initial']['E']
    assert q['energy_balance_error']<.005

def test_stress_source_zero_mode_periodic():
    q=periodic_stress_monopole(providers(96)['gilbert']['x'],24)
    assert q['k_zero']==0
    assert abs(q['source_integral'])<1e-10
    assert not q['poisson_periodic_nonzero_monopole_allowed']

def test_two_independent_curves_short_time_smoke(tmp_path):
    z=run_dynamic(tmp_path,mode='BASIC')
    assert set(z['providers'])=={'gilbert','knotplot'}
    assert z['qualification']['status']=='PASS'
    assert len(z['local_dynamic_gates'])==7
    assert (tmp_path/'V050_DYNAMIC_RESULTS.json').exists()

def test_claims_and_version_guards():
    assert 'v0.5.0' in (ROOT/'falsifier.toml').read_text()
    gp=json.loads((ROOT/'gate_plan.json').read_text()); assert 'G10' in [g['gate_id'] for g in gp['gates']]
    assert 'LOCAL_VALIDATED_CANDIDATE' in (ROOT/'README.md').read_text()
    p=json.loads((ROOT/'science_contract.json').read_text())
    assert any('universal gravity' in str(x).lower() for x in p['assumptions'])
    assert '6.67430e-11' not in (ROOT/'microgravity/dynamic_campaign_v050.py').read_text()
    nonce=ROOT/'private/REVEAL_NONCE.bin'
    assert not nonce.exists() or nonce.stat().st_size==32

def test_keeps_framework_secret_initialize_once():
    s=(ROOT/'init_private.py').read_text()
    assert 'secrets.token_bytes(32)' in s
    assert 'if not p.exists()' in s
    assert 'already exist' in s
