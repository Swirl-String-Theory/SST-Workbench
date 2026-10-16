from __future__ import annotations
import argparse, sys, tempfile, json
from pathlib import Path
import numpy as np
from common import dump, read, guard, digest, unique, sha_record

BASE=Path(__file__).resolve().parent
PFILE=BASE/'protocol.json'

def load_rpo(path):
    with np.load(path,allow_pickle=False) as f:
        guard({'x0','xT','rotation','shift_points'}<=set(f.files),
          'RPO NPZ must include x0,xT,rotation,shift_points')
        x0=np.asarray(f['x0'],dtype=np.float64)
        xT=np.asarray(f['xT'],dtype=np.float64)
        R=np.asarray(f['rotation'],dtype=np.float64)
        shift=int(f['shift_points'])
        translation=np.asarray(f['translation'],dtype=np.float64) if 'translation' in f else np.zeros(3)
        M=np.asarray(f['monodromy'],dtype=np.float64) if 'monodromy' in f else None
    guard(x0.ndim==2 and x0.shape[1]==3 and x0.shape[0]>=3,'Invalid RPO points')
    guard(xT.shape==x0.shape and np.isfinite(xT).all() and np.isfinite(x0).all(),'Nonfinite/inconsistent state')
    guard(R.shape==(3,3) and np.linalg.norm(R.T@R-np.eye(3))<1e-8 and np.linalg.det(R)>0.999,
        'rotation must be proper orthogonal SO(3)')
    if M is not None:
        d=x0.size
        guard(M.shape==(d,d) and np.isfinite(M).all(),'Full-state tangent-map monodromy dimensions do not match RPO')
    guard(translation.shape==(3,) and np.isfinite(translation).all(),'Translation vector malformed')
    return x0,xT,R,shift,translation,M

def act(x,R,shift,translation=None):
    return np.roll(x,shift,axis=0) @ R.T + (np.zeros(3) if translation is None else translation)

def inverse_on_tangent(M,R,shift,n):
    # For xT = shift(x0) * R^T, map final perturbations to initial coordinates: S^{-1}.
    d=3*n
    resh=M.reshape(n,3,d)
    back=np.roll(resh,-shift,axis=0)
    back=np.einsum('ij,njk->nik',R.T,back)
    return back.reshape(d,d)

def check_rpo(npz_path,meta_path=None,mode='CHECK'):
    cfg=read(PFILE)
    x0,xT,R,shift,translation,M=load_rpo(npz_path)
    closure=float(np.linalg.norm(xT-act(x0,R,shift,translation))/max(np.linalg.norm(x0),1e-14))
    row={
        'version':'A045-v0.3.0','source':sha_record(npz_path),'mode':mode,
        'RPO_closure_rel':closure,'state_dof':int(x0.size),
        'finite_core_ladder':'REQUIRES_ORIGINAL_A045_EXTENDED_RUN',
        'python_native_parity':'REQUIRES_ORIGINAL_A045_WINDOWS_RUN',
        'monodromy_present':M is not None,
        'gates':{}
    }
    g=row['gates']
    g['G0_SOURCE_AUTHENTICITY']='UNRESOLVED'
    g['G1_RPO_GEOMETRIC_CLOSURE']='PASS' if closure<=cfg['rpo_closure_rel_max'] else 'FAIL'
    g['G2_UPSTREAM_INDEPENDENCE']='UNRESOLVED'
    g['G3_TIME_SPACE_CONVERGENCE']='UNRESOLVED'
    g['G4_FULL_TANGENT_MAP']='UNRESOLVED'
    g['G5_TRANSVERSE_FLOQUET']='NOT_RUN'
    g['G6_EULER_PHYSICS']='UNRESOLVED'
    if mode=='CERTIFY':
        guard(meta_path and Path(meta_path).exists(),'CERTIFY requires upstream metadata JSON')
        meta=read(meta_path)
        guard(meta.get('source_sha256')==digest(npz_path),'Upstream NPZ hash mismatch')
        guard(meta.get('source_class') in ('E011_PKLSA','A031_RPO','A038_RPO','INDEPENDENT_EULER_RPO'),
            'Unknown upstream source class')
        g['G0_SOURCE_AUTHENTICITY']='PASS_HASH_ONLY'
        qualified=(meta.get('certified_rpo') is True and
            meta.get('held_out') is True and
            bool(meta.get('independence_group')) and
            meta.get('blind_commitment_verified') is True)
        g['G2_UPSTREAM_INDEPENDENCE']='PASS_UPSTREAM_ATTESTED' if qualified else 'UNRESOLVED'
        checks=meta.get('convergence',{})
        nums=('closure_refined','timestep_ratio','mesh_refined','tangent_fd_parity')
        valid=all(isinstance(checks.get(k), (float,int)) for k in nums)
        if valid:
            valid=(checks['closure_refined']<=cfg['rpo_closure_rel_max'] and
                checks['timestep_ratio']>=2 and checks['mesh_refined']<=cfg['mesh_rel_max'] and
                checks['tangent_fd_parity']<=cfg['tangent_parity_max'])
        g['G3_TIME_SPACE_CONVERGENCE']='PASS_UPSTREAM_ATTESTED' if valid else 'UNRESOLVED'
    if M is not None:
        d=x0.size
        if d>cfg['max_eigendecomposition_dof']:
            g['G4_FULL_TANGENT_MAP']='UNRESOLVED_TOO_LARGE_FOR_REFERENCE_EIGENSOLVER'
        else:
            F=inverse_on_tangent(M,R,shift,len(x0))
            eig=np.linalg.eigvals(F)
            mag=np.sort(np.abs(eig))
            row['spectral_radius_all']=float(mag[-1])
            row['multipliers_abs_sorted']=mag.tolist()
            near=np.abs(np.abs(eig)-1)<cfg['neutral_band']
            row['neutral_candidates']=int(near.sum())
            if mode=='CERTIFY':
                checks=meta.get('convergence',{})
                if (meta.get('full_tangent') is True and checks.get('tangent_fd_parity',1e9)<=cfg['tangent_parity_max']):
                    g['G4_FULL_TANGENT_MAP']='PASS_UPSTREAM_ATTESTED'
            # No automatic dismissal of numerical unit multipliers: neutral count and subspace must be certified.
            if all(g[k].startswith('PASS') for k in ('G0_SOURCE_AUTHENTICITY','G1_RPO_GEOMETRIC_CLOSURE',
                        'G2_UPSTREAM_INDEPENDENCE','G3_TIME_SPACE_CONVERGENCE','G4_FULL_TANGENT_MAP')):
                n_neutral=meta.get('neutral_multiplicities_verified')
                if isinstance(n_neutral,int) and n_neutral==int(near.sum()) and n_neutral>0:
                    max_transverse=max(np.abs(eig[~near]),default=0.0)
                    row['spectral_radius_transverse']=float(max_transverse)
                    g['G5_TRANSVERSE_FLOQUET']='PASS_LINEAR_MODEL' if max_transverse<=1+cfg['transverse_growth_tol'] else 'FAIL_INSTABILITY'
                else:g['G5_TRANSVERSE_FLOQUET']='UNRESOLVED_NEUTRAL_SUBSPACE'
    row['physics_verdict']='UNTESTED' if g['G5_TRANSVERSE_FLOQUET'] in ('NOT_RUN','UNRESOLVED_NEUTRAL_SUBSPACE') else 'UNRESOLVED'
    output=unique(BASE/'outputs','A045v030')
    dump(output/'CHECK_RESULT.json',row)
    dump(output/'SOURCE_MANIFEST.json',{'rpo':sha_record(npz_path),
        'upstream_provenance':sha_record(meta_path) if meta_path else None,'protocol':sha_record(PFILE)})
    print(output, '\n'+json.dumps(g,indent=2))
    return row


def search_trajectory(path):
    # An exploratory RPO candidate finder on actual time-dependent upstream PKLSA/Euler geometry.
    # No source of physical dynamics here, and no Floquet without independent full tangent map.
    with np.load(path,allow_pickle=False) as f:
        guard('times' in f and 'positions' in f,'Expected times and positions arrays')
        times=np.asarray(f['times'],dtype=float)
        xs=np.asarray(f['positions'],dtype=float)
    guard(xs.ndim==3 and xs.shape[-1]==3 and len(times)==len(xs) and len(xs)>=4,
          'Expected (frames,points,3) and times')
    guard(xs.shape[1]>=16 and np.all(np.isfinite(xs)) and np.all(np.diff(times)>0),
          'Invalid curve time history')
    x0=xs[0];n=len(x0); nt=len(xs)
    candidates=np.unique(np.linspace(max(2,nt//4),nt-1,min(nt-2,32),dtype=int))
    shifts=np.unique(np.linspace(0,n-1,min(n,64),dtype=int))
    best=None
    for j in candidates:
        target=xs[j]
        for k in shifts:
            src=np.roll(x0,int(k),axis=0)
            cm=src.mean(axis=0);tm=target.mean(axis=0)
            A=(src-cm).T@(target-tm)
            U,_,V=np.linalg.svd(A)
            Q=U@np.diag([1,1,np.linalg.det(U@V)])@V  # row action rotation
            trans=tm-cm@Q
            err=float(np.linalg.norm(src@Q+trans-target)/max(1e-14,np.linalg.norm(target-tm)))
            if best is None or err<best['error']:
                best={'error':err,'frame_index':int(j),'shift':int(k),'rotation':Q.T,'translation':trans}
    guard(best is not None,'Candidate search empty')
    out=unique(BASE/'candidate_outputs','A045candidate')
    candidate=out/'UPSTREAM_CANDIDATE_UNCERTIFIED.npz'
    np.savez(candidate,x0=x0,xT=xs[best['frame_index']],rotation=best['rotation'],
              translation=best['translation'],shift_points=best['shift'])
    dump(out/'CANDIDATE_SEARCH.json',{
        'trajectory':sha_record(path),'candidate_npz':sha_record(candidate),
        'candidate_period_source_units':float(times[best['frame_index']]-times[0]),
        'relative_shape_closure':best['error'],'frame_index':best['frame_index'],
        'shift_points':best['shift'],'n_frames':int(nt),'n_points':int(n),
        'scope':'RPO_SEARCH_CANDIDATE_NOT_CERTIFIED','floquet':'NOT_RUN',
        'caveat':'kabsch best-fit group action and finite grid/search can create near-closures'})
    print(out,'Candidate closure:',best['error'], '\\nFloquet NOT_RUN. Independently certify upstream before CERTIFY.')

def selftest():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'mock.npz';n=4
        t=np.linspace(0,2*np.pi,n,endpoint=False)
        x=np.stack([np.cos(t),np.sin(t),np.zeros_like(t)],axis=1)
        np.savez(p,x0=x,xT=x,rotation=np.eye(3),shift_points=0,monodromy=np.eye(3*n))
        row=check_rpo(p)
        assert row['gates']['G1_RPO_GEOMETRIC_CLOSURE']=='PASS'
        assert row['gates']['G5_TRANSVERSE_FLOQUET']=='NOT_RUN'
        # invalid RPO must reject symmetry and nonzero closure
        np.savez(p,x0=x,xT=x+0.2,rotation=np.eye(3),shift_points=0)
        row=check_rpo(p)
        assert row['gates']['G1_RPO_GEOMETRIC_CLOSURE']=='FAIL'
    print('A045 SELFTEST PASS (mock state); no physical Floquet certification')

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['SELFTEST','SEARCH','CHECK','CERTIFY'])
    p.add_argument('--rpo');p.add_argument('--trajectory');p.add_argument('--meta');a=p.parse_args()
    if a.mode=='SELFTEST':selftest();return
    if a.mode=='SEARCH':
        guard(a.trajectory,'Provide --trajectory path to actual time-dependent upstream NPZ')
        search_trajectory(a.trajectory);return
    guard(a.rpo is not None,'Provide --rpo <upstream RPO .npz>')
    check_rpo(a.rpo,a.meta,a.mode)
if __name__=='__main__':
    try:main()
    except Exception as e:print('FAIL-CLOSED:',e,file=sys.stderr);sys.exit(2)
