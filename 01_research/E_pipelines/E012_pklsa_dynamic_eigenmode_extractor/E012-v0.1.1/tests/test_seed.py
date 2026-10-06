import json, gzip
from pathlib import Path
from e012_dynamic.seed import parse_gilbert_ab, sample_gilbert, select_anchor

def test_parse_and_sample_gilbert(tmp_path):
    p=tmp_path/"Ideal.txt.gz"
    text='''<AB Id="3:1:1" Conway="3" L="6.0" D=" 1.0">
    <Coeff I=" 1" A=" 1,0,0" B=" 0,1,0" />
    <Coeff I=" 2" A=" 0.2,0,0.3" B=" 0,0.2,0" />
    </AB>'''
    with gzip.open(p,"wt",encoding="utf-8") as f: f.write(text)
    m=parse_gilbert_ab(p,"3:1:1")
    x=sample_gilbert(m,24)
    assert x.shape==(24,3)
    assert m.D==1.0

def test_anchor_selection(tmp_path):
    p=tmp_path/"seed.json"
    p.write_text(json.dumps({
      "summary":{"static_ready":True,"topology_id":"3_1"},
      "provider_anchors":[
        {"provider_group":"gilbert","static_ready":True,"source_locator":{"representation":"gilbert_ab_record"}}
      ]
    }))
    a,s=select_anchor(p,("gilbert",))
    assert a["provider_group"]=="gilbert"
