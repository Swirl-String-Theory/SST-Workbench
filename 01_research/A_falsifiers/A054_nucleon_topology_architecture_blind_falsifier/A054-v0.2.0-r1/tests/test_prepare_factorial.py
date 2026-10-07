import numpy as np
import a054_ntaf.prepare as pm


def _curve(n=96,phase=0.0):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[(2+.5*np.cos(3*t+phase))*np.cos(2*t),
                 (2+.5*np.cos(3*t+phase))*np.sin(2*t),
                 .5*np.sin(3*t+phase)]


def test_full_factorial_case_count_one_provider_stratum(tmp_path,monkeypatch):
    anchors={
      '5_2':{'index':{},'anchors':[{'provider_group':'p52','static_seed_id':'s52'}]},
      '6_1':{'index':{},'anchors':[{'provider_group':'p61','static_seed_id':'s61'}]},
      'L6a4':{'index':{},'anchors':[]},
    }
    monkeypatch.setattr(pm,'audit_required_topologies',lambda wb:anchors)
    monkeypatch.setattr(pm,'materialize_anchor_geometry',lambda a,wb,n:_curve(n,0 if a['static_seed_id']=='s52' else .2))
    # This test checks factorial bookkeeping; geometry construction itself is covered elsewhere.
    monkeypatch.setattr(pm,'_build_factor_geometry',lambda code,bits,k52,k61,skeletons,n:(skeletons[code],{'class':'mock'}))
    wb=tmp_path/'wb'; wb.mkdir()
    out=tmp_path/'out'; status=pm.prepare(out,wb,n=48)
    assert status['status']=='PREPARED_FULL'
    assert status['candidate_count']==27  # 3 controls + 3 skeletons * 8 binary assignments * 1 provider stratum
