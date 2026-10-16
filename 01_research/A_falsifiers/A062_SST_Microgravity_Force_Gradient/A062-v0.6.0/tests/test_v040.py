import json,hashlib,sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from microgravity.geometry import providers
from microgravity.energy_transport_v050 import kernel_energy,enstrophy_kernel,gaussian_divergence_quadrature,run
from microgravity.filament import RHO_F,R_C,GAMMA

def test_e011_raw_pins():
    pins=json.loads((ROOT/'inputs/e011/provider_pins.json').read_text())
    for item in pins['provider_anchors']:
        assert hashlib.sha256((ROOT/item['file']).read_bytes()).hexdigest()==item['raw_sha256']

def test_closed_loop_divergence_exact():
    for d in providers(96).values():
        x=d['x'];a=d['metadata']['reach']
        q=gaussian_divergence_quadrature(x,a,np.array([[.1,.04,.02],[-.06,.13,-.03]]),12)
        assert max(abs(k)*a**4 for k in q)<1e-5
        assert np.linalg.norm((np.roll(x,-1,axis=0)-x).sum(axis=0))<1e-12

def test_energy_convergence_and_positivity():
    coarse=providers(128);fine=providers(256)
    for g in ('gilbert','knotplot'):
        a=fine[g]['metadata']['reach']
        c=kernel_energy(coarse[g]['x'],a)
        f=kernel_energy(fine[g]['x'],a)
        assert c>0 and f>0
        assert abs(c-f)/f<.007
        assert enstrophy_kernel(fine[g]['x'],a)>0

def test_no_newton_G_in_solver():
    src=(ROOT/'microgravity/energy_transport_v050.py').read_text()
    assert '6.67430e-11' not in src

def test_reader_epistemic_guard():
    info=json.loads((ROOT/'inputs/SST_KNOWLEDGE_CENSUS.json').read_text())
    assert len(info['articles'])==91
    assert info['articles'][28]['reading_status']=='EXCLUDED_BY_USER'
    assert any(k['reading_status']=='INDEXED_NOT_READ' for k in info['articles'])

def test_instance_framework_pin_and_private_nonce_guard():
    assert (ROOT/'.sst_framework_root').read_text().strip().endswith('SST_Falsifier_Framework_v1.0.8')
    s=(ROOT/'init_private.py').read_text()
    assert "secrets.token_bytes(32)" in s and "if not p.exists()" in s
    nonce=ROOT/'private/REVEAL_NONCE.bin'
    assert not nonce.exists() or nonce.stat().st_size==32

def test_source_is_conditional_not_prediction():
    p=json.loads((ROOT/'science_contract.json').read_text())
    assert any('do not prove universal gravity' in x.lower() for x in p['assumptions'])
    assert any('No Newtonian G' in x for x in p['assumptions'])

def test_run_basic_smoke(tmp_path):
    result=run(tmp_path,mode='BASIC')
    gate={q['gate']:q['status'] for q in result['scientific_gates']}
    assert gate['V1']=='PASS'
    assert gate['V2']=='PASS'
    assert gate['V3']=='PASS'
    assert gate['V4']=='FAIL'
    assert gate['V8']=='UNRESOLVED'
    assert (tmp_path/'V050_SCIENCE_RESULTS.json').exists()
