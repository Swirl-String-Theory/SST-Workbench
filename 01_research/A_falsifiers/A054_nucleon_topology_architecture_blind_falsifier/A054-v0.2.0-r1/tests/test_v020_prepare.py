import numpy as np
import a054_ntaf.prepare_v020 as pm


def _curve(n=72,phase=0.0):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.c_[(2+.5*np.cos(3*t+phase))*np.cos(2*t),(2+.5*np.cos(3*t+phase))*np.sin(2*t),.5*np.sin(3*t+phase)]


def test_basic_same_provider_cohort_count(tmp_path,monkeypatch):
    anchors={
      '5_2':{'index':{},'anchors':[{'provider_group':'gilbert','static_seed_id':'g52'},{'provider_group':'knotplot','static_seed_id':'k52'}]},
      '6_1':{'index':{},'anchors':[{'provider_group':'gilbert','static_seed_id':'g61'},{'provider_group':'knotplot','static_seed_id':'k61'}]},
      'L6a4':{'index':{},'anchors':[]}}
    monkeypatch.setattr(pm,'audit_required_topologies',lambda wb:anchors)
    monkeypatch.setattr(pm,'write_upstream_plan',lambda wb,out: out.write_text('{}'))
    monkeypatch.setattr(pm,'materialize_anchor_geometry',lambda a,wb,n:_curve(n,0.0 if a['provider_group']=='gilbert' else .2))
    monkeypatch.setattr(pm,'_build_factor_geometry',lambda code,bits,k52,k61,skeletons,n:(skeletons[code],{'class':'mock'}))
    wb=tmp_path/'wb'; wb.mkdir(); out=tmp_path/'out'
    m=pm.prepare_certification(out,wb,n=36,preset='basic')
    # linked: 2 skeletons * 6 mixed bits * 2 same-provider strata = 24
    # U controls: 2 canonical mixed bits * 2 strata = 4
    assert m['candidate_count']==28
    assert m['scientific_ready'] is True
