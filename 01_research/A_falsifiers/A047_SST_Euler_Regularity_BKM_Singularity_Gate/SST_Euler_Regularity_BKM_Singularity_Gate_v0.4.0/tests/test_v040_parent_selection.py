import json
from pathlib import Path
from sst_bkm.parent_v030 import select_parent_blind, reveal_parent_selection


def _j(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj),encoding='utf-8')


def test_parent_selection_is_blind_deterministic_and_reveal_late(tmp_path):
    root=tmp_path/'v030'; b=root/'BLIND'; r=root/'REVEALED'; b.mkdir(parents=True); r.mkdir()
    runs=[]; reveal={}
    for i,(g,grp,growth,r2,ts) in enumerate([
        ('g1','A',1.4,.7,.8),('g2','A',1.2,.99,.7),('g3','B',1.5,.8,.6),('g4','C',1.1,.5,1.2)
    ]):
        runs.append({'case_id':f'c{i}','geometry_id':g,'group_id':grp,'T':.18,'omega_growth':growth,'numerically_valid':True,'blowup_fit':{'r2':r2,'t_star':ts}})
        reveal[g]={'e010_carrier_id':f'CAR_{i}','source_family':'SECRET'}
    _j(b/'summary.json',{'assessment':{'verdict':'X'},'runs':runs}); _j(b/'run_manifest.json',{'x':1}); _j(r/'case_reveal_map.json',reveal)
    a=select_parent_blind(root,{'max_geometries':4}); b2=select_parent_blind(root,{'max_geometries':4})
    assert a['selection_sha256']==b2['selection_sha256']
    assert all('source_family' not in x for x in a['selected'])
    assert len({x['group_id'] for x in a['selected'][:3]})==3
    rr=reveal_parent_selection(root,a)
    assert rr['selection_sha256']==a['selection_sha256'] and len(rr['selected'])==4
