import math, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_ladder_definition():
    cfg=json.loads((ROOT/'configs/default.json').read_text())['ladder']
    assert cfg['k_min']==-16 and cfg['k_max']==16 and cfg['delta_log2']==0.25 and cfg['include_zero_endpoint'] is True
    vals={k:2.0**(k/4.0) for k in range(-16,17)}
    for k in range(1,17): assert math.isclose(vals[k]*vals[-k],1.0,rel_tol=0,abs_tol=2e-15)
