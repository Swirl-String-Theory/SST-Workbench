from pathlib import Path
from .util import read_json
from .upstream import verify_framework_output

def summarize_v031(out:Path):
    verify_framework_output(out,'FULL'); o=read_json(Path(out)/'A055_SIGNED_TRAVEL_BLIND.json')
    pos=neg=qualified=both_sector=0
    for r in o.get('rows',[]):
        dirs=[]
        for m in r.get('signed_travel',{}).get('traveling_candidates',[]):
            if m.get('qualifies'):
                qualified+=1; d=int(m.get('direction',0)); dirs.append(d); pos+=d>0; neg+=d<0
        if 1 in dirs and -1 in dirs: both_sector+=1
    return {'schema':'A055-V031-DISCOVERY-BASELINE-040','qualified_traveling_components':qualified,'positive_direction_components':pos,'negative_direction_components':neg,
            'sectors_with_both_directions':both_sector,'source_output':str(out),'guard':'Discovery baseline only; raw signed direction is representation-dependent and is not the v0.4.0 decision statistic.'}
