from pathlib import Path
import argparse,json,hashlib
import numpy as np
p=argparse.ArgumentParser(description='Convert a generic PKLSA NPZ into the A056 blind provider contract.')
p.add_argument('source'); p.add_argument('destination'); p.add_argument('--t-key',default='t'); p.add_argument('--s-key',default='s'); p.add_argument('--phi-key',default='phi'); p.add_argument('--ringdown-key',default=None); p.add_argument('--ringdown-t-key',default=None); p.add_argument('--opaque-id',required=True); p.add_argument('--source-group',required=True); p.add_argument('--boundary',choices=['periodic','open'],default='periodic'); a=p.parse_args()
src=Path(a.source); z=np.load(src,allow_pickle=False); kw={'t':np.asarray(z[a.t_key],float),'s':np.asarray(z[a.s_key],float),'phi':np.asarray(z[a.phi_key],float)}
if a.ringdown_key: kw['ringdown']=np.asarray(z[a.ringdown_key],float)
if a.ringdown_t_key: kw['ringdown_t']=np.asarray(z[a.ringdown_t_key],float)
dst=Path(a.destination); dst.parent.mkdir(parents=True,exist_ok=True); np.savez_compressed(dst,**kw)
h=hashlib.sha256(src.read_bytes()).hexdigest(); meta={'opaque_id':a.opaque_id,'source_group':a.source_group,'boundary':a.boundary,'upstream_sha256':h}; dst.with_suffix('.json').write_text(json.dumps(meta,indent=2),encoding='utf-8'); print(dst)
