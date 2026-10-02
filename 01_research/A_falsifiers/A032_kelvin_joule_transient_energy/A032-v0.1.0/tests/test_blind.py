import json
from pathlib import Path
import numpy as np
from kj_sst.blind import prepare

def test_blind_public_manifest_has_no_source_name(tmp_path):
 d=tmp_path/'data';d.mkdir();t=np.linspace(0,2*np.pi,80,endpoint=False);p=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)];np.savetxt(d/'secret_trefoil_name.txt',p)
 out=tmp_path/'campaign';cfg={'resolutions':[32]};prepare(d,out,cfg)
 public=(out/'blind_manifest.public.json').read_text();assert 'secret_trefoil_name' not in public
 private=(out/'blind_manifest.private.json').read_text();assert 'secret_trefoil_name' in private
 frozen=json.loads((out/'frozen_protocol.json').read_text());assert len(frozen['config_sha256'])==64
