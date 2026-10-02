from pathlib import Path
import hashlib,json
import numpy as np
import pytest
from sst_torsion.pklsa import load_trefoil_population

def test_pklsa_shape_non_strict(tmp_path):
    (tmp_path/'families').mkdir(); (tmp_path/'manifests').mkdir()
    pts=np.zeros((48,1,512,3),float)
    t=np.linspace(0,2*np.pi,512,endpoint=False)
    pts[:,:, :,0]=np.cos(t)[None,None,:]
    pts[:,:, :,1]=np.sin(t)[None,None,:]
    np.savez(tmp_path/'families'/'14_knot_3p1.npz',points=pts)
    rows=[{'family':'knot_3.1','canonical_id':'3_1','family_index':14,'variant_index':i} for i in range(48)]
    (tmp_path/'manifests'/'CANDIDATES_FULL.jsonl').write_text('\n'.join(json.dumps(r) for r in rows),encoding='utf-8')
    pop,d=load_trefoil_population(tmp_path,strict_hash=False)
    assert pop.shape==(48,512,3)
    assert len(d)==64

@pytest.mark.parametrize('fault',['empty','duplicate','inconsistent','nonfinite','wrong_shape'])
def test_manifest_and_coordinate_contract_rejects_invalid_inputs(tmp_path,fault):
    test_pklsa_shape_non_strict(tmp_path)
    manifest=tmp_path/'manifests'/'CANDIDATES_FULL.jsonl'
    rows=[json.loads(line) for line in manifest.read_text().splitlines()]
    if fault=='empty':
        rows=[]
    elif fault=='duplicate':
        rows[-1]['variant_index']=0
    elif fault=='inconsistent':
        rows[0]['canonical_id']='4_1'
    else:
        bundle=tmp_path/'families'/'14_knot_3p1.npz'
        with np.load(bundle) as z:
            p=z['points']
        if fault=='nonfinite':
            p[0,0,0,0]=np.nan
        else:
            p=p[:47]
        np.savez(bundle,points=p)
    manifest.write_text('\n'.join(json.dumps(row) for row in rows))
    with pytest.raises(ValueError):
        load_trefoil_population(tmp_path,strict_hash=False)
