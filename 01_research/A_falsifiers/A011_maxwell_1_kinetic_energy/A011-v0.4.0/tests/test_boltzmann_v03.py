import math

from maxwell_sst_falsifier.boltzmann import (
    boltzmann_occupation_audit,
    log_multinomial_complexions,
    microcanonical_temperature,
    state_count_entropy_force,
)
from maxwell_sst_falsifier.constants import EV_J, K_B_J_PER_K


def test_log_multinomial_known():
    # 7!/(4!2!1!) = 105
    assert math.isclose(log_multinomial_complexions([4,2,1]), math.log(105.0), rel_tol=1e-12)


def test_boltzmann_fit_recovers_temperature():
    T=300.0; beta=EV_J/(K_B_J_PER_K*T)
    rows=[]
    for i,(e,g) in enumerate([(0.0,1),(0.01,2),(0.02,1),(0.03,3)]):
        rows.append({'ensemble_id':'e','knot':'3_1','invariant_sector':'s','state_id':str(i),'energy_eV':str(e),'occupation':str(1e6*g*math.exp(-beta*e)),'degeneracy':str(g)})
    r=boltzmann_occupation_audit(rows,T,0.01,0.999)[0]
    assert r['status']=='PASS'
    assert abs(r['T_fit_K']-T)/T < 1e-10


def test_entropy_force_and_microcanonical_temperature():
    T=300.0; beta=EV_J/(K_B_J_PER_K*T); F=1e-12; alpha=F/(K_B_J_PER_K*T)
    rows=[]
    for x in [-1e-9,0,1e-9]:
        for e in [0.0,0.01,0.02]:
            rows.append({'series_id':'s','knot':'k','invariant_sector':'i','x_m':str(x),'energy_eV':str(e),'log_state_count':str(100+alpha*x+beta*e),'T_eff_K':str(T)})
    f=state_count_entropy_force(rows,T)
    assert len(f)==9
    assert max(abs(x['F_entropic_N']-F) for x in f if x['status']=='COMPUTED') < 1e-24
    mt=microcanonical_temperature(rows)
    assert len(mt)==3
    assert max(abs(x['T_micro_K']-T) for x in mt) < 1e-8


def test_maximum_permutability_selects_even_distribution():
    from maxwell_sst_falsifier.boltzmann import permutability_audit, maximum_permutability_audit
    rows=[]
    for eid,obs,vals in [
        ('even',True,[('x0',0.0,30),('x0',0.01,20),('x1',0.0,30),('x1',0.01,20)]),
        ('uneven',False,[('x0',0.0,50),('x0',0.01,10),('x1',0.0,10),('x1',0.01,30)]),
    ]:
        for j,(x,e,w) in enumerate(vals):
            rows.append({'macrostate_id':'m','ensemble_id':eid,'observed':'true' if obs else 'false','knot':'k','invariant_sector':'i','position_bin':x,'energy_bin':f'e{int(e>0)}','energy_eV':str(e),'occupation':str(w),'degeneracy':'1'})
    p=permutability_audit(rows)
    r=maximum_permutability_audit(rows,p)[0]
    assert r['status']=='PASS'
    assert 'even' in r['maximizing_ensembles']
