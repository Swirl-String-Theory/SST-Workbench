import json
from pathlib import Path
import numpy as np
from a055_spectrum.providers import parse_xyz, select_provider_anchors

def test_xyz_parser_headers_comments_and_duplicate_close(tmp_path):
    p=tmp_path/"curve.txt"
    p.write_text("""# x y z
header ignored
0 0 0
1,0,0 extra
1 1 0 # comment
0 1 0
0 0 0
""")
    x=parse_xyz(p)
    assert x.shape==(4,3)
    assert np.allclose(x[1],[1,0,0])

def test_single_provider_is_explicit_not_exception(tmp_path):
    p=tmp_path/"STATIC_READY_SEEDSET.json"
    obj={
      "summary":{"topology_id":"X","static_ready":True},
      "provider_anchors":[
        {"provider_group":"gilbert","static_ready":True,"carrier_id":"A"}
      ]
    }
    p.write_text(json.dumps(obj))
    anchors,summary,cov=select_provider_anchors(p,("gilbert","knotplot"),"X",True)
    assert len(anchors)==1
    assert cov["status"]=="SINGLE_PROVIDER_ONLY"
    assert cov["missing_provider_groups"]==["knotplot"]

def test_full_provider_set(tmp_path):
    p=tmp_path/"STATIC_READY_SEEDSET.json"
    obj={
      "summary":{"topology_id":"X","static_ready":True},
      "provider_anchors":[
        {"provider_group":"gilbert","static_ready":True,"carrier_id":"A"},
        {"provider_group":"knotplot","static_ready":True,"carrier_id":"B"}
      ]
    }
    p.write_text(json.dumps(obj))
    anchors,summary,cov=select_provider_anchors(p,("gilbert","knotplot"),"X",True)
    assert len(anchors)==2
    assert cov["status"]=="FULL_PROVIDER_SET"
