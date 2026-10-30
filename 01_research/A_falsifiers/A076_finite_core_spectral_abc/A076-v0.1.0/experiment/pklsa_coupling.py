"""PKLSA geometry/dynamical C pilot: rigorously *not* a topology certificate.
No Fourier-m labels are transferred from circular rings to arbitrary knots.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import numpy as np


def dig(a):return hashlib.sha256(np.ascontiguousarray(a,dtype='<f8').tobytes()).hexdigest()


def velocity(vertices, core):
    """Regularized midpoint finite-core Biot-Savart; one closed component.
    Native dimensionless coords; no periodic images or external field in this pilot.
    """
    v=np.asarray(vertices,dtype=np.float64)
    dl=np.roll(v,-1,axis=0)-v
    mids=.5*(np.roll(v,-1,axis=0)+v)
    rr=v[:,None,:]-mids[None,:,:]
    d=(np.einsum('ijk,ijk->ij',rr,rr)+core*core)**(-1.5)
    return (np.cross(dl[None,:,:],rr)*d[:,:,None]).sum(axis=1)/(4*math.pi)



def mutual_velocity(target, source, core, batch=64):
    """Cross-filament Biot--Savart, original vertices, no interpolation.

    Chunked to prevent O(N_target*N_source) temporary-memory explosion.
    A measured nonzero coupling alone is NOT C hierarchy evidence.
    """
    target=np.asarray(target,dtype=np.float64)
    source=np.asarray(source,dtype=np.float64)
    dl=np.roll(source,-1,axis=0)-source
    mid=.5*(np.roll(source,-1,axis=0)+source)
    out=np.empty_like(target)
    for a0 in range(0,len(target),batch):
        r=target[a0:a0+batch,None,:]-mid[None,:,:]
        den=(np.einsum('ijk,ijk->ij',r,r)+core*core)**(-1.5)
        out[a0:a0+batch]=(np.cross(dl[None,:,:],r)*den[:,:,None]).sum(axis=1)/(4*math.pi)
    return out


def relative_residual(p,u):
    center=p.mean(axis=0);x=p-center
    # least-squares v = translation + omega cross (x - mean(x)).
    n=len(p);M=np.zeros((3*n,6));M[:,0:3]=np.tile(np.eye(3),(n,1))
    for i,(xx,yy,zz) in enumerate(x):
        M[3*i:3*i+3,3:]=[[0,zz,-yy],[-zz,0,xx],[yy,-xx,0]]
    coef,*_=np.linalg.lstsq(M,u.reshape(-1),rcond=None)
    residual=np.linalg.norm(u.reshape(-1)-M@coef)/max(np.linalg.norm(u),1e-30)
    return float(residual),{'translation':coef[:3].tolist(),'omega':coef[3:].tolist()}


def euler_step(p,core,dt):
    # Heun/RK2 (diagnostic only): test time-step consistency, not Euler PDE closure.
    v0=velocity(p,core);pred=p+dt*v0
    return p+.5*dt*(v0+velocity(pred,core))


def evolve(p,core,dt,total=0.02):
    steps=round(total/dt)
    if abs(steps*dt-total)>1e-10:raise ValueError('different final time')
    x=p.copy()
    for _ in range(steps):x=euler_step(x,core,dt)
    return x


def assess_c_dataset(root,out,mode):
    root=Path(root);out=Path(out)
    pin=root/'input'/'C_PKLSA_PIN.json'
    if not pin.exists():return {'status':'C_NOT_EVALUATED','reason':'No verified E010 consumer export pinned before freeze'}
    spec=json.loads(pin.read_text(encoding='utf8'))
    if spec.get('atlas')!='E010-v0.4.0' or spec.get('adapter')!='v0.1.0':
        raise ValueError('unsupported E010/PKLSA pin')
    from pklsa_bridge import ConsumerDataset
    ds=ConsumerDataset(root/'input'/'e010_export')
    if ds.verification.get('status')!='PASS_DATASET_INTEGRITY_ONLY':
        raise RuntimeError('PKLSA dataset integrity gate failed')
    if ds.verification.get('manifest_sha256')!=spec['manifest_sha256']:
        raise RuntimeError('E010 manifest SHA256 changed')
    all_ids=ds.list_ids()
    if sorted(all_ids)!=sorted(spec['record_ids']):
        raise RuntimeError('E010 set of pinned records changed')
    records=[]
    for rec_id in all_ids:
        comps=ds.load(rec_id)
        meta=ds.metadata(rec_id)
        parts=[]
        for comp in comps:
            p=np.asarray(comp,dtype=np.float64)
            if p.ndim!=2 or p.shape[1]!=3 or len(p)<16 or not np.isfinite(p).all():
                raise ValueError('invalid geometry component')
            radius=float(np.max(np.linalg.norm(p-p.mean(axis=0),axis=1)))
            if radius<=0:raise ValueError('degenerate geometry radius')
            a=.04*radius
            if len(p)>1024:
                parts.append({'raw_sha256':dig(p),'n':len(p),'status':'UNRESOLVED_MEMORY_CAP',
                              'reason':'do not silently resample E010 vertices'});continue
            u=velocity(p,a)
            external=np.zeros_like(u)
            coupled_parts=0
            for other_index, other in enumerate(comps):
                if other_index==len(parts):continue
                src=np.asarray(other,dtype=np.float64)
                if src.ndim!=2 or src.shape[1]!=3 or len(src)>1024:
                    continue
                external+=mutual_velocity(p,src,a)
                coupled_parts+=1
            res,rigid=relative_residual(p,u+external)
            diag={'raw_sha256':dig(p),'n':len(p),'finite_core_ratio':.04,
                  'relative_rigid_residual':res,'rigid_fit':rigid,
                  'cross_component_coupling_ratio':float(np.linalg.norm(external)/max(np.linalg.norm(u),1e-30)),
                  'cross_component_sources':coupled_parts,
                  'operator':'original-index midpoint regularized Biot-Savart, no mesh resampling'}
            if mode.upper() in ('FULL','CERTIFY') and res<.05:
                x1=evolve(p,a,.01);x2=evolve(p,a,.005)
                diag['dt_test']={'dt1':.01,'dt2':.005,'final_time':.02,
                    'relative_difference':float(np.linalg.norm(x1-x2)/max(np.linalg.norm(x2),1e-30)),
                    'interpretation':'two-step discretization diagnostic; not proven temporal convergence'}
            parts.append(diag)
        records.append({'record_id':rec_id,'source_metadata':meta,'components':parts})
    payload={'status':'C_PILOT_DIAGNOSTIC_ONLY','records':records,
             'n_records':len(records),'independent_source_groups_qualified':0,
             'spatial_convergence':'NOT_EVALUATED',
             'coupled_eigenmodes':'NOT_EVALUATED',
             'static_intercomponent_coupling':'MEASURED_FOR_MULTICOMPONENT_RECORDS_ONLY',
             'scale_hierarchy':'NOT_EVALUATED',
             'note':'Even a small relative residual is not a free Euler equilibrium, knot invariance or C proof.'}
    target=out/'abc_science'/'C_PKLSA_DIAGNOSTICS.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(payload,indent=2,default=str,allow_nan=False)+'\n',encoding='utf8')
    return payload
