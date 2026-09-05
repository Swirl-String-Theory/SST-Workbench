from pathlib import Path
import numpy as np,json
from sst_phase_delay_falsifier.blind import prepare

def test_blind_names_removed(tmp_path):
    inp=tmp_path/'in'; out=tmp_path/'blind'; inp.mkdir()
    t=np.linspace(0,2*np.pi,30,endpoint=False); x=np.c_[np.cos(t),np.sin(t),.2*np.sin(3*t)]
    np.savetxt(inp/'charge60_i10000.txt',x)
    reg=tmp_path/'reg.json'; reg.write_text(json.dumps({'canonical64_sha256':[]}))
    audit=prepare(inp,out,'*_i10000.txt',24,128,64,'legacy_audit',reg,1)
    assert audit['n_selected_unique']==1
    pub=(out/'sealed_manifest.json').read_text(); assert 'charge60' not in pub
    key=(out.parent/'private_reveal'/'reveal_key.json').read_text(); assert 'charge60' in key
