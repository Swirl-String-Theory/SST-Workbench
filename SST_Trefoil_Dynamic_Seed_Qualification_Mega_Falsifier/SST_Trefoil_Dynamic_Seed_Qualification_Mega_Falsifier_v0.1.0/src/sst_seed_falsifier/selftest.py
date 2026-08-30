import tempfile,json
from pathlib import Path
import numpy as np
from .candidates import analytic_trefoil
from .geometry import resample_closed,normalize_length,align_cyclic,rigid_normal_fit,fourier_normal_basis
from .solver import velocity_from_cores,velocity_py,backend_name

def run(require_native=False):
    x=normalize_length(resample_closed(analytic_trefoil(256),64),2*np.pi); cores=np.full(len(x),.08); up=velocity_py(x,1.0,cores); un=velocity_from_cores(x,1.0,cores,require_native); rel=float(np.linalg.norm(up-un)/max(np.linalg.norm(up),1e-15)); a,d,sh,R,t=align_cyclic(x,x,4); B,L=fourier_normal_basis(x,2); rf=rigid_normal_fit(x,un); ok=rel<1e-11 and d<1e-12 and len(B)>=4 and np.isfinite(rf['coherence']); print(json.dumps({'backend':backend_name(),'native_python_rel_l2':rel,'self_alignment':d,'basis_dim':len(B),'rolling_coherence':rf['coherence'],'PASS':bool(ok)},indent=2)); return 0 if ok else 1
