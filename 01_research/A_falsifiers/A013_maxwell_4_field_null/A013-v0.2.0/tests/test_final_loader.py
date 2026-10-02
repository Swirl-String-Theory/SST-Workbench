import json, numpy as np
from maxwell_sst.geometry import load_curve_set
def test_multicomponent_txt_with_metrics(tmp_path):
    p=tmp_path/'link_6.3.3_final.txt'; a=np.arange(27,dtype=float).reshape(9,3); np.savetxt(p,a)
    (tmp_path/'link_6.3.3_final.metrics.json').write_text(json.dumps({'component_count':3,'vertices_per_component':[3,3,3]}))
    cs=load_curve_set(p); assert len(cs.components)==3 and all(len(c)==3 for c in cs.components)
