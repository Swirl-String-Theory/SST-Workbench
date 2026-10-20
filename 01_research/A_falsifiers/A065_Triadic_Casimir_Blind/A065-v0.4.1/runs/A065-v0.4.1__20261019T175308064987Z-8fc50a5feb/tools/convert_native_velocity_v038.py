"""Convert AUTHENTIC periodic u(x,t) into ω=curl u, without any Gaussian core assumption.

This script does not independently validate its upstream producer. It refuses
unknown boundary conditions and records upstream hashes and operator details.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import numpy as np

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def convert(input_path,source_json,output_path):
    input_path=Path(input_path);source_json=Path(source_json);output_path=Path(output_path)
    meta=json.loads(source_json.read_text(encoding='utf-8'))
    for key in ['schema','source_sha256','provider','solver_commit','run_id','time','units','dx','boundary_conditions']:
        if key not in meta:raise ValueError('MISSING_UPSTREAM_FIELD_'+key)
    if digest(input_path)!=meta['source_sha256']:raise ValueError('UPSTREAM_SHA256_MISMATCH')
    if meta['boundary_conditions']!='periodic':raise ValueError('NO_UNDECLARED_BC_CONVERSION')
    if input_path.suffix.lower()=='.npy':U=np.load(input_path,allow_pickle=False)
    else:
        with np.load(input_path,allow_pickle=False) as z:
            if 'u' not in z:raise ValueError('MISSING_U')
            U=z['u']
    U=np.asarray(U,dtype=np.float64)
    if U.ndim!=4 or U.shape[0]!=3 or len(set(U.shape[1:]))!=1 or not np.isfinite(U).all():raise ValueError('INVALID_VELOCITY_GRID')
    n=U.shape[1];dx=float(meta['dx']);rho=float(meta.get('rho',1.))
    if n<16 or dx<=0 or not np.isfinite(dx):raise ValueError('INVALID_GRID_SPACING')
    K=np.meshgrid(*([2*np.pi*np.fft.fftfreq(n,d=dx)]*3),indexing='ij')
    uh=np.fft.fftn(U,axes=(1,2,3))
    w_hat=np.array([1j*(K[1]*uh[2]-K[2]*uh[1]),1j*(K[2]*uh[0]-K[0]*uh[2]),1j*(K[0]*uh[1]-K[1]*uh[0])])
    W=np.fft.ifftn(w_hat,axes=(1,2,3)).real
    pressure=None
    div=np.fft.ifftn(1j*sum(K[i]*uh[i] for i in range(3))).real
    output_path.parent.mkdir(parents=True,exist_ok=True)
    with output_path.open('xb') as fh:np.savez_compressed(fh,omega=W,u=U,dx=np.float64(dx),rho=np.float64(rho))
    record={'schema':'A065-V038-CONVERSION-AUDIT-1','input_sha256':digest(input_path),
           'input_metadata_sha256':digest(source_json),'output_sha256':digest(output_path),
           'upstream_source_class':meta.get('source_class','NOT_PROVIDED'),
           'claimed_provider':meta['provider'],'operator':'periodic spectral curl; NOT finite-core inference',
           'divergence_u_rms':float(np.sqrt(np.mean(div**2))),
           'independent_velocity_pressure_holdout':'NOT_PROVIDED',
           'physical_pklsa_certification':'UNRESOLVED_SOURCE_AUDIT_REQUIRED'}
    audit=output_path.with_suffix('.audit.json')
    with audit.open('x') as f:json.dump(record,f,indent=2,sort_keys=True);f.write('\n')
    return record
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--velocity',required=True)
    p.add_argument('--upstream-manifest',required=True)
    p.add_argument('--output',required=True)
    args=p.parse_args()
    print(json.dumps(convert(args.velocity,args.upstream_manifest,args.output),indent=2))
