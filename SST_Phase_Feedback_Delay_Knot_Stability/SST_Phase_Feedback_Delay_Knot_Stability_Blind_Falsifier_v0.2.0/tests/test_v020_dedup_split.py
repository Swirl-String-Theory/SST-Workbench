import json
from pathlib import Path
import numpy as np
from sst_phase_delay_falsifier.blind import prepare
from sst_phase_delay_falsifier.analysis import grouped_split,fit_negative_linear

def circle(n=40,r=1.0,zamp=0.1):
 t=np.linspace(0,2*np.pi,n,endpoint=False); return np.c_[r*np.cos(t),r*np.sin(t),zamp*np.sin(3*t)]
def write(p,x): np.savetxt(p,x)
def test_dedup_before_blind(tmp_path):
 inp=tmp_path/'in';out=tmp_path/'blind';inp.mkdir(); x=circle();write(inp/'A_i10000.txt',x);write(inp/'B_i10000.txt',x);write(inp/'C_i10000.txt',circle(r=1.1))
 reg=tmp_path/'reg.json';reg.write_text(json.dumps({'canonical64_sha256':[]}))
 a=prepare(inp,out,'*_i10000.txt',64,128,64,'legacy_audit',reg,2)
 assert a['n_source_files']==3 and a['n_unique_before_novelty']==2 and a['n_duplicate_files_removed']==1
 man=json.loads((out/'sealed_manifest.json').read_text()); assert len(man['items'])==2
 key=json.loads((tmp_path/'private_reveal/reveal_key.json').read_text()); assert sorted(q['duplicate_count'] for q in key['items'])==[1,2]
def test_split_deterministic_and_balanced():
 hs=[f'{i:064x}' for i in range(10)]; a=grouped_split(hs,3,3);b=grouped_split(hs,3,3)
 assert np.array_equal(a,b); assert a.sum()>=3 and (~a).sum()>=3
def test_negative_linear_constraint():
 D=np.arange(6.0);Y=10-2*D; a,b=fit_negative_linear(D,Y); assert b<0; assert np.allclose(a+b*D,Y)
