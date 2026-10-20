"""PKLSA phase-clock scientific preflight (NOT framework certification).
No SST target frequency, Lorentz factor, or phase is an input.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from scipy.signal import hilbert

MIN_CYCLES=6.0
MAX_PHASE_RMSE_RAD=0.20
MAX_INST_FREQ_CV=0.12
MAX_CROSS_FREQ_REL=0.03


def measure_scalar_clock(t, q):
    t=np.asarray(t,dtype=float)
    q=np.asarray(q,dtype=float)
    if t.ndim!=1 or q.shape!=t.shape or len(t)<128:
        return {"status":"INDETERMINATE", "reason":"time series missing or too short"}
    d=np.diff(t)
    if not (np.all(np.isfinite(t)) and np.all(np.isfinite(q)) and np.all(d>0)):
        return {"status":"INVALID", "reason":"nonfinite data or nonmonotone time"}
    if np.std(d)/np.mean(d)>1e-5:
        return {"status":"INDETERMINATE", "reason":"nonuniform time requires preregistered resampling"}
    if np.ptp(q)<1e-8:
        return {"status":"NO_CLOCK", "reason":"constant observable: rigid-body rotations cannot count"}
    analytic=hilbert(q-np.mean(q))
    n=len(t); a=max(10,int(n*0.1)); b=n-a
    phase=np.unwrap(np.angle(analytic))
    tm=t[a:b]; pm=phase[a:b]
    freq=np.polyfit(tm,pm,1)[0]
    if not np.isfinite(freq) or abs(freq)<1e-12:
        return {"status":"NO_CLOCK","reason":"non-running phase"}
    fit=freq*tm+np.polyfit(tm,pm,1)[1]
    phase_rmse=float(np.sqrt(np.mean((pm-fit)**2)))
    inst=np.diff(pm)/np.diff(tm)
    cv=float(np.std(inst)/max(abs(float(np.mean(inst))),1e-12))
    cycles=float(abs((pm[-1]-pm[0])/(2*np.pi)))
    measured={"omega":float(freq), "frequency":float(freq/(2*np.pi)),
              "phase_rmse_rad":phase_rmse,"instantaneous_frequency_cv":cv,
              "cycles_observed":cycles}
    stable=(cycles>=MIN_CYCLES and phase_rmse<=MAX_PHASE_RMSE_RAD and cv<=MAX_INST_FREQ_CV)
    measured["status"]="COHERENT_NUMERICAL_SCREEN" if stable else "SCREEN_FAIL"
    return measured


def compare_two(t,q1,q2):
    a,b=measure_scalar_clock(t,q1),measure_scalar_clock(t,q2)
    good=a['status']==b['status']=='COHERENT_NUMERICAL_SCREEN'
    rel=abs(a['omega']-b['omega'])/max(abs(a['omega']),abs(b['omega'])) if good else None
    return {"q1":a,"q2":b,"cross_frequency_relative_error":rel,
            "G3_phase_reproducibility":"PASS_NUMERICAL_ONLY" if good and rel<=MAX_CROSS_FREQ_REL else "SCREEN_FAIL"}


def extract_shape_invariants(u, domain_length, mask=None):
    """Compute *rotation-invariant* enstrophy shape time series from periodic 3D Euler u.
    This is a numerical screening observable only. A certified material tube mask,
    phase-space gauge and independent operator prediction are still required.
    """
    u=np.asarray(u,dtype=float)
    if u.ndim!=5 or u.shape[-1]!=3 or len(set(u.shape[1:4]))!=1:
        raise ValueError("u must be (nt, n, n, n, 3) on cubic periodic grid")
    if not np.all(np.isfinite(u)) or domain_length<=0: raise ValueError('bad u or L')
    nt,n,_,_,_=u.shape
    k=2*np.pi*np.fft.fftfreq(n,d=domain_length/n)
    kx,ky,kz=np.meshgrid(k,k,k,indexing='ij')
    # enstrophy-weighted periodic circular centroid
    vals=[]; divergence=[]
    x=np.arange(n)*domain_length/n
    if mask is not None and np.asarray(mask).shape!=(nt,n,n,n):
        raise ValueError("mask must be (nt,n,n,n)")
    for it in range(nt):
        uf=np.fft.fftn(u[it],axes=(0,1,2)); fx,fy,fz=uf[...,0],uf[...,1],uf[...,2]
        w=np.stack((np.fft.ifftn(1j*(ky*fz-kz*fy)).real,
                    np.fft.ifftn(1j*(kz*fx-kx*fz)).real,
                    np.fft.ifftn(1j*(kx*fy-ky*fx)).real),axis=-1)
        div=np.fft.ifftn(1j*(kx*fx+ky*fy+kz*fz)).real
        divergence.append(float(np.sqrt(np.mean(div**2))))
        wt=np.einsum('...i,...i->...',w,w)
        if mask is not None: wt=wt*np.maximum(np.asarray(mask)[it],0)
        mass=float(np.sum(wt))
        if mass<=0: raise ValueError("zero enstrophy in observation mask")
        centered=[]
        for axis in range(3):
            marg=np.sum(wt,axis=tuple(j for j in range(3) if j!=axis))
            z=np.sum(marg*np.exp(2j*np.pi*x/domain_length))
            centroid=float(np.angle(z)*domain_length/(2*np.pi))
            delta=(x-centroid+domain_length/2)%domain_length-domain_length/2
            shape=[1,1,1];shape[axis]=n
            centered.append(delta.reshape(shape))
        C=np.array([[np.sum(wt*centered[i]*centered[j])/mass for j in range(3)] for i in range(3)])
        eig=np.linalg.eigvalsh(C)[::-1]
        vals.append([(eig[0]-eig[1])/sum(eig),(eig[1]-eig[2])/sum(eig)])
    vals=np.array(vals)
    return vals[:,0],vals[:,1],{"divergence_rms_max_raw_units":float(max(divergence)),"remark":"full box periodic centering; requires isolated certified tube mask"}


def demo():
    t=np.linspace(0,80,4001)
    f0=0.25 # SYNTHETIC control only; not a hypothesized vortex frequency
    ph=2*np.pi*f0*t
    trials={
        'positive_two_shape_signals':compare_two(t,0.08*np.sin(ph),0.05*np.cos(ph+0.3)),
        'negative_rigid_rotation_shape_invariants':compare_two(t,np.ones_like(t)*0.2,np.ones_like(t)*0.1),
        'negative_beating':compare_two(t,0.08*(np.sin(ph)+0.85*np.sin(1.18*ph)),0.05*np.cos(ph))
    }
    trials['control_notes']=['The positive oscillator is synthetic, not Euler or PKLSA evidence.',
      'Rigid rotation does not alter rotationally invariant shape observables.',
      'Beating is a test of non-single-frequency interference.']
    return trials


def audit_A064(filename):
    r=json.loads(Path(filename).read_text(encoding='utf-8'))
    return {"source":Path(filename).name,"sha256":hashlib.sha256(Path(filename).read_bytes()).hexdigest(),
         "prior_conclusion":r.get('overall'),"reported_physical_gates":r.get('scientific_gates'),
         "G0_real_PKLSA_clock_data":"UNRESOLVED_GEOMETRY_ONLY",
         "G1_periodic_relative_equilibrium":"UNRESOLVED",
         "G2_two_independent_intrinsic_3D_shape_signals":"NOT_PROVIDED",
         "G3_phase_frequency":"NOT_TESTABLE",
         "G4_operator_prediction_holdout":"NOT_TESTABLE",
         "G5_mesh_timestep_core_convergence":"UNRESOLVED",
         "G6_independent_provider":"UNRESOLVED",
         "overall":"NO_PHYSICAL_CLOCK_INFERENCE_POSSIBLE"}


def run_npz(filename):
    with np.load(filename, allow_pickle=False) as z:
        t=z['t']; u=z['u']; L=float(z['domain_length'])
        q1,q2,diag=extract_shape_invariants(u,L,z['material_mask'] if 'material_mask' in z.files else None)
        rv=compare_two(t,q1,q2)
        rv['observable']='enstrophy covariance eigenvalue gaps; translation/rotation invariant on periodic cube'
        rv['field_diagnostics']=diag
        rv['physical_status']='UNRESOLVED_PENDING_SOURCE_MASK_EULER_INTEGRITY_RELATIVE_ORBIT_OPERATOR_AND_CONVERGENCE'
    return rv


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--a064',type=Path)
    p.add_argument('--field-npz',type=Path)
    p.add_argument('--out',type=Path,default=Path('outputs/PREFLIGHT_RESULTS.json'))
    a=p.parse_args()
    results={"schema":"sst-pklsa-phaseclock-preflight-0.1.0", "test_type":"UNBLINDED_METHOD_DEVELOPMENT_NOT_PHYSICAL_VALIDATION", "demo":demo()}
    if a.a064: results['existing_A064_source_audit']=audit_A064(a.a064)
    if a.field_npz: results['user_3D_fields_screen']=run_npz(a.field_npz)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({"output":str(a.out),"positive":results['demo']['positive_two_shape_signals']['G3_phase_reproducibility'],
                      "rigid":results['demo']['negative_rigid_rotation_shape_invariants']['G3_phase_reproducibility'],
                      "beating":results['demo']['negative_beating']['G3_phase_reproducibility'],
                      "physical":"UNRESOLVED"}))

if __name__=='__main__': main()
