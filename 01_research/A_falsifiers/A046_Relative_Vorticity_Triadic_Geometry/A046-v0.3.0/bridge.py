from __future__ import annotations
import argparse, csv, json, sys, math, tempfile
from pathlib import Path
import numpy as np
from common import dump, read, guard, sha_record, digest, unique

BASE=Path(__file__).resolve().parent
CONFIG=BASE/'protocol.json'

def curve(path):
    p=Path(path);guard(p.exists(),'Missing native PKLSA CSV source')
    with p.open(encoding='utf-8-sig',newline='') as f:
        first=f.readline().strip()
    if first.lower().replace(' ','').startswith(('x,y,z','x;y;z')):
        sep=';' if ';' in first else ','
        rows=[]
        with p.open(encoding='utf-8-sig',newline='') as f:
            dr=csv.DictReader(f,delimiter=sep)
            for row in dr: rows.append([float(row[k]) for k in ('x','y','z')])
        a=np.array(rows,dtype=float)
    else:
        a=np.loadtxt(p,delimiter=',',dtype=float)
        if a.ndim==1: a=a.reshape(1,-1)
        a=a[:,:3]
    guard(a.ndim==2 and a.shape[1]==3 and a.shape[0]>=16,'Curve must have >=16 3D points')
    guard(np.isfinite(a).all(),'Nonfinite knot geometry')
    if np.linalg.norm(a[0]-a[-1])<1e-10: a=a[:-1]
    seg=np.roll(a,-1,axis=0)-a
    guard(np.linalg.norm(seg,axis=1).min()>1e-10,'Degenerate zero-length segment')
    # Blind dimensional normalization, preserve the original scaling separately.
    extent=np.linalg.norm(a.max(axis=0)-a.min(axis=0))
    guard(extent>0,'Zero extent')
    return (a-a.mean(axis=0))/extent,extent

def induced(points, x, a, box, chunk=2048):
    seg=np.roll(x,-1,axis=0)-x
    mid=x+0.5*seg
    out=np.zeros_like(points,dtype=np.float64)
    # Rosenhead regularized midpoint quadrature. Not periodic Biot-Savart.
    for s in range(0,len(points),chunk):
        dp=points[s:s+chunk,None,:]-mid[None,:,:]
        den=(np.sum(dp*dp,axis=-1)+a*a)**1.5
        out[s:s+chunk]=np.sum(np.cross(seg[None,:,:],dp)/den[:,:,None],axis=1)/(4*np.pi)
    return out

def spectral(u,L):
    n=u.shape[0]
    k=2*np.pi*np.fft.fftfreq(n,d=L/n)
    kk=np.meshgrid(k,k,k,indexing='ij')
    K=np.stack(kk,axis=-1)
    K2=np.sum(K*K,axis=-1)
    U=np.fft.fftn(u,axes=(0,1,2))
    dot=np.sum(U*K,axis=-1)
    P=U-np.where(K2[...,None]>0,K*dot[...,None]/np.maximum(K2[...,None],1e-300),0)
    proj=np.fft.ifftn(P,axes=(0,1,2)).real
    d=np.stack([np.fft.ifftn(1j*K[...,i,None]*P,axes=(0,1,2)).real for i in range(3)],axis=-2)
    # d_(i,j) = d u_j/d x_i ; div = trace(d)
    div=np.trace(d,axis1=-2,axis2=-1)
    strain=(d+np.swapaxes(d,-1,-2))/2
    omega=np.stack([d[...,1,2]-d[...,2,1],d[...,2,0]-d[...,0,2],d[...,0,1]-d[...,1,0]],axis=-1)
    # Pressure-Poisson in dimensionless rho=1: Laplace(p)=-sum_ij (partial_i u_j)(partial_j u_i)
    source=-np.einsum('...ij,...ji->...',d,d)
    S=np.fft.fftn(source)
    Phat=-np.where(K2>0,S/np.maximum(K2,1e-300),0)
    p=np.fft.ifftn(Phat).real
    lap=np.fft.ifftn(-K2*Phat).real
    residual=lap-(source-source.mean())
    denom=max(1e-30,float(np.linalg.norm(source-source.mean())))
    gradrel=float(np.linalg.norm(residual)/denom)
    normgrad=np.maximum(1e-30,np.linalg.norm(d))
    recon=strain+0.5*(d-np.swapaxes(d,-1,-2))
    return {
        'divergence_rel':float(np.linalg.norm(div)/normgrad),
        'pressure_poisson_rel':gradrel,
        'strain_rms':float(np.sqrt(np.mean(np.einsum('...ij,...ij->...',strain,strain)))),
        'vorticity_rms':float(np.sqrt(np.mean(np.sum(omega**2,axis=-1)))),
        'reconstruction_rel':float(np.linalg.norm(recon-d)/normgrad),
        'projected_velocity_rms':float(np.sqrt(np.mean(proj**2))),
        'projection_change_rel':float(np.linalg.norm(proj-u)/max(1e-30,np.linalg.norm(u))),
        'pressure_rms':float(np.sqrt(np.mean(p*p))),
        'poisson_zero_mode':float(source.mean())
    }

def compute(curve_path,config):
    x,original_span=curve(curve_path)
    a=float(config['softening']); L=float(config['domain_length']);ns=list(config['grids'])
    guard(a>0 and L>1.2,'invalid geometric configuration')
    out={}
    for n in ns:
        guard(8<=n<=128 and n%2==0,'Invalid grid n')
        z=-L/2+L*np.arange(n)/n
        pts=np.stack(np.meshgrid(z,z,z,indexing='ij'),axis=-1).reshape(-1,3)
        vel=induced(pts,x,a,L).reshape((n,n,n,3))
        diag=spectral(vel,L)
        diag['n']=n;diag['boundary_class']='free_space_sampled_then_periodic_projection'
        out[str(n)]=diag
    n0,n1=map(str,ns[-2:]) if len(ns)>1 else (str(ns[0]),str(ns[0]))
    relative=abs(out[n1]['vorticity_rms']-out[n0]['vorticity_rms'])/max(1e-30,out[n1]['vorticity_rms'])
    return {'grids':out,'grid_refinement_vorticity_rel':relative,'original_span_in_source_units':original_span,
        'source_sha256':digest(curve_path),'source_points':int(len(x))}

def protocol():return read(CONFIG)

def certify(inp, meta, mode):
    P=protocol()
    guard(Path(inp).exists(),'PKLSA CSV required')
    if mode=='CERTIFY':
        guard(meta is not None and Path(meta).exists(),'CERTIFY requires independent upstream metadata file')
        M=read(meta)
        for k in ('source_class','upstream_sha256','independence_group','topology'):
            guard(bool(M.get(k)),f'Missing source provenance field {k}')
        guard(M['source_class']=='E011_PKLSA','CERTIFY rejects unqualified source classes')
        guard(M['upstream_sha256']==digest(inp),'Upstream hash mismatch')
    else:M={}
    res=compute(inp,P)
    highest=res['grids'][str(P['grids'][-1])]
    gates={
        'G0_SOURCE_HASH': 'PASS' if (mode!='CERTIFY' or M['upstream_sha256']==res['source_sha256']) else 'FAIL',
        'G1_SOLENOIDAL_PROJECTION': 'PASS' if highest['divergence_rel']<=P['tol_divergence'] else 'FAIL',
        'G2_PRESSURE_POISSON_ALGEBRA': 'PASS' if highest['pressure_poisson_rel']<=P['tol_poisson'] else 'FAIL',
        'G3_UWS_FIRST_ORDER_RECONSTRUCTION': 'PASS' if highest['reconstruction_rel']<=P['tol_reconstruction'] else 'FAIL',
        'G4_GRID_CONVERGENCE': 'PASS' if res['grid_refinement_vorticity_rel']<=P['tol_grid_rel'] else 'FAIL',
        'G5_BOUNDARY_PHYSICAL_CLOSURE':'UNRESOLVED',
        'G6_EULER_TIME_EVOLUTION':'NOT_RUN',
        'G7_INDEPENDENT_PROVIDER_REPLICATION':'UNRESOLVED',
        'G8_GRAVITY_PREDICTION':'UNRESOLVED',
    }
    if mode!='CERTIFY':gates['G0_SOURCE_HASH']='DIAGNOSTIC_ONLY'
    res['gates']=gates;res['physics_verdict']='UNRESOLVED';res['mode']=mode
    res['source_class_reported']=M.get('source_class','UNVERIFIED');res['provenance_asserted_not_verified']=bool(M)
    run=unique(BASE/'outputs','A046v030')
    dump(run/'BLIND_RESULT.json',res)
    dump(run/'SOURCE_MANIFEST.json',{'geometry':sha_record(inp),'metadata':sha_record(meta) if meta else None,
      'protocol':sha_record(CONFIG),'interpretation':'input identity not used as a result target'})
    print(run, '\n',json.dumps(gates,indent=2))
    return run

def make_demo(directory):
    t=np.linspace(0,2*np.pi,80,endpoint=False)
    x=np.stack([np.cos(t),np.sin(t),0*t],axis=1)
    np.savetxt(directory/'synthetic_circle.csv',x,delimiter=',',header='x,y,z',comments='')
    return directory/'synthetic_circle.csv'

def selftest():
    with tempfile.TemporaryDirectory() as td:
        path=make_demo(Path(td));cfg=protocol()
        res=compute(path,{**cfg,'grids':[8,12]})
        for k in ('divergence_rel','pressure_poisson_rel','reconstruction_rel'):
            assert res['grids']['12'][k]<1e-7,(k,res['grids']['12'][k])
        assert res['grid_refinement_vorticity_rel']>=0
    print('A046 diagnostic implementation SELFTEST PASS (synthetic circle only); physical campaign NOT_RUN')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['SELFTEST','DRYRUN','CERTIFY'])
    p.add_argument('--csv');p.add_argument('--meta')
    a=p.parse_args()
    if a.mode=='SELFTEST':selftest();return
    guard(a.csv is not None,'Pass actual E011/PKLSA --csv path')
    certify(a.csv,a.meta,a.mode)
if __name__=='__main__':
    try:main()
    except Exception as e:print(f'FAIL-CLOSED: {e}',file=sys.stderr);sys.exit(2)
