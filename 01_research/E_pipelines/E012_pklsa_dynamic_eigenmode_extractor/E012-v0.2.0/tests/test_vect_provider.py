import json
import numpy as np
from pathlib import Path
from e012_dynamic.seed import parse_vect, resample_closed, select_provider_anchors

def test_parse_closed_vect(tmp_path):
    p=tmp_path/'k.vect'
    p.write_text('''VECT\n1 4 0\n-4\n0\n0 0 0\n1 0 0\n1 1 0\n0 1 0\n''')
    x=parse_vect(p)
    assert x.shape==(4,3)
    y=resample_closed(x,16)
    assert y.shape==(16,3)

def test_select_two_provider_anchors(tmp_path):
    p=tmp_path/'seed.json'
    p.write_text(json.dumps({'summary':{'static_ready':True,'topology_id':'3_1'},'provider_anchors':[
      {'provider_group':'gilbert','static_ready':True},{'provider_group':'knotplot','static_ready':True}
    ]}))
    a,s=select_provider_anchors(p,('gilbert','knotplot'))
    assert [x['provider_group'] for x in a]==['gilbert','knotplot']
