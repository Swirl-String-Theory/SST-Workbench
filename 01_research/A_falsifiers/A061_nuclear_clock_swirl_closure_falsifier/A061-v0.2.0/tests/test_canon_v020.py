import numpy as np
import pytest
from a061.canon_v020 import (C_SI,V_SWIRL,H_SI,canon_factor,legacy_factor,action_phase,spectro_gap,lock_window,pinning_energy,pinning_stationary_minima,phase_jump_countermodel,common_ratio)

def test_clock_domains():
    assert canon_factor(0)==1
    assert 0<canon_factor(V_SWIRL)<1
    assert legacy_factor(.5*V_SWIRL)!=canon_factor(.5*V_SWIRL)
    with pytest.raises(ValueError): canon_factor(C_SI)
    with pytest.raises(ValueError): legacy_factor(V_SWIRL)

def test_action_phase_limits():
    rel,f=action_phase([0.,1.,1e7]);assert np.allclose(rel,f);assert f[0]==1 and f[-1]<1e-6

def test_spectro_dimensions():
    assert spectro_gap(2.0204e15)/H_SI==pytest.approx(2.0204e15)

def test_adler_window():
    assert lock_window(100.2,100,.3) and not lock_window(102,100,.3)

def test_q_spectrum():
    for q in (0,2,3,4,5,6,8):
        minima=pinning_stationary_minima(q)
        assert len(minima)==q
        assert np.allclose(pinning_energy(minima,q),0,atol=1e-12)

def test_clock_independent_frequency_shift():
    t=np.linspace(0.,2.,2001); _,f=phase_jump_countermodel(t,10,2,1)
    assert np.median(f[100:800])==pytest.approx(10)
    assert np.median(f[1200:1800])==pytest.approx(12)

def test_common_factor_cancellation():
    assert common_ratio(3,.8)==pytest.approx(3)
    assert common_ratio(3,.8,1.01,1.)!=pytest.approx(3)

def test_gates_registered():
    import json
    from pathlib import Path
    r=Path(__file__).resolve().parents[1];d=json.loads((r/'gate_plan.json').read_text())
    assert {f'G{k}' for k in range(14,22)}.issubset({g['gate_id'] for g in d['gates']})
    assert all(not g['requires'] for g in d['gates'])

def test_revision_not_reused_freeze():
    from pathlib import Path
    r=Path(__file__).resolve().parents[1]
    assert 'v0.2.0' in (r/'falsifier.toml').read_text()
    assert (r/'docs/CANON_v0.8.36_EXTRACT.md').is_file()
