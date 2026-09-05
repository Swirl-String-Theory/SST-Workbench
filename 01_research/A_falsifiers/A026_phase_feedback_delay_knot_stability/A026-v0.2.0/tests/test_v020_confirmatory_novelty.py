import json,hashlib
import numpy as np
from sst_phase_delay_falsifier.blind import prepare
from sst_phase_delay_falsifier.geometry import resample_closed

def test_confirmatory_filters_historical_geometry(tmp_path):
    inp=tmp_path/'in'; out=tmp_path/'blind'; inp.mkdir()
    t=np.linspace(0,2*np.pi,50,endpoint=False); x=np.c_[np.cos(t),np.sin(t),.2*np.sin(3*t)]
    np.savetxt(inp/'old_i10000.txt',x)
    y=resample_closed(x,64); h=hashlib.sha256(np.ascontiguousarray(y,dtype='<f8').tobytes()).hexdigest()
    reg=tmp_path/'reg.json'; reg.write_text(json.dumps({'canonical64_sha256':[h]}))
    audit=prepare(inp,out,'*_i10000.txt',64,128,64,'confirmatory',reg,1)
    assert audit['n_historical_seen_unique']==1
    assert audit['n_selected_unique']==0
    assert not list(out.glob('B*.npy'))
