import json
from pathlib import Path
from sst_trpl.synthetic import make_reference_panel,energy,integrate
from sst_trpl.evaluation import evaluate

def test_reference_energy_and_qualification():
    root=Path(__file__).resolve().parents[1]; cfg=json.loads((root/'configs/default.json').read_text())
    m,t,e,en=make_reference_panel(n_pairs=12,steps=2500,dt=0.01,seed=5101)
    # lower balance minimum only inside test fixture; scientific default remains frozen at 20
    cfg= json.loads(json.dumps(cfg)); cfg['thresholds']['seed_balance_min_n']=20
    r=evaluate(m,t,e,en,cfg)
    assert r['verdict']=='QUALIFIED_INSTRUMENT_ONLY'
    assert r['gates']['G5_TR_PAIR_ANTISYMMETRY']['status']=='PASS'
    assert r['gates']['G6_BRANCH_DEGENERACY']['status']=='PASS'

def test_integrator_energy_drift_small():
    t,phi,p=integrate(1.4,0.08,1.0,0.005,5000); h=energy(phi,p,1.0)
    assert (h.max()-h.min())/(abs(h.mean())+1e-15)<2e-4
