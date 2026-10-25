"""Topology-Preserving Directed Energy Transfer: DEVELOPMENT ONLY.

Uses original midpoint Rosenhead filament dynamics vendored from
Borromean_Blind_Clock_Falsifier_v0.1.0. Not a field Euler solver.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, os, secrets, random
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'src'))
from geometry import arclength_resample,parse_xyz,pair_linking,perimeter
from dynamics import rk4,native_available
from segment_geometry import network_segment_clearance

REGISTRY={
  'RING_CONTROL': 'analytic_leapfrog',
  'TREFOIL': 'trefoil_3_1',
  'TORUS': 'torus_2_5',
  'BORROMEAN': 'borromean_ideal'
}

def sha(data:bytes):return hashlib.sha256(data).hexdigest()

def ring(n,r,z):
    t=2*np.pi*np.arange(n)/n
    return np.column_stack([r*np.cos(t),r*np.sin(t),np.full(n,z)])

def normalize_geometry(cs,n):
    # Global common length unit chosen by RMS radius about whole-source centroid.
    cs=[arclength_resample(np.asarray(c,dtype=np.float64),n) for c in cs]
    xyz=np.concatenate(cs);center=xyz.mean(axis=0)
    scale=np.sqrt(np.mean(np.sum((xyz-center)**2,axis=1)))
    if scale<=0:raise ValueError('degenerate geometry')
    return [(c-center)/scale for c in cs]

def load_source(key,n):
    if key=='analytic_leapfrog':
        return [ring(n,.9,-.15),ring(n,1.1,.15)], [1.,1.], 'matched_two_ring_baseline'
    if key=='trefoil_3_1':
        source=(ROOT/'seeds/trefoil_3_1_source.xyz').read_bytes()
        # XYZ may contain blank blocks and comments; format verified on load.
        cs=normalize_geometry(parse_xyz(source),n)
    else:
        p=ROOT/'seeds'/f'{key}_native.npz'
        with np.load(p,allow_pickle=False) as z:
            cs=normalize_geometry([z[f'c{i}'] for i in range(len(z.files))],n)
    # Common receiver; its placement beyond source z-extent prevents initial overlap.
    # This gap is identical for all arms, but global scale, component count, circulation
    # and donor shapes differ: no topology-specific performance attribution allowed.
    top=max(float(x[:,2].max()) for x in cs)
    cs=[x+np.array([0.,0.,-1.0]) for x in cs]
    receiver=ring(n,1.0,top-1.0+0.8)
    return cs+[receiver], [1.]*len(cs)+[1.], 'exploratory_common_receiver'

def hamiltonian(cs,gamma,core):
    """Discrete regularized line-integral Hamiltonian proxy, rho=1.

    1/(8*pi) sum_ij Gamma_i Gamma_j \u222b\u222b dr_i.dr_j /sqrt(|r_i-r_j|²+a²).
    It is NOT a spatial-region Euler energy-flux diagnostic.
    """
    n=len(cs); mat=np.zeros((n,n))
    mids=[]; dl=[]
    for x in cs:
        edge=np.roll(x,-1,axis=0)-x
        mids.append(.5*(x+np.roll(x,-1,axis=0)));dl.append(edge)
    for i in range(n):
        for j in range(i,n):
            a=mids[i];b=mids[j]
            diff=a[:,None,:]-b[None,:,:]
            den=np.sqrt(np.einsum('ijk,ijk->ij',diff,diff)+core*core)
            dot=np.einsum('ik,jk->ij',dl[i],dl[j])
            val=gamma[i]*gamma[j]*float(np.sum(dot/den))/(8*np.pi)
            mat[i,j]=mat[j,i]=val
    return float(mat.sum()),np.diag(mat).tolist(),float(mat.sum()-np.trace(mat)),mat.tolist()

def clearance_proxy(cs):
    # Vertex distance only, NOT certified continuous segment clearance.
    ans=float('inf')
    for i in range(len(cs)):
        for j in range(i+1,len(cs)):
            ai=cs[i];bj=cs[j]
            for start in range(0,len(ai),32):
                v=ai[start:start+32,None,:]-bj[None,:,:]
                ans=min(ans, float(np.sqrt(np.min(np.sum(v*v,axis=-1)))))
    return ans

def linking_matrix(cs):
    n=len(cs);a=np.zeros((n,n),float)
    for i in range(n):
        for j in range(i+1,n):a[i,j]=a[j,i]=pair_linking(cs[i],cs[j])
    return a.tolist()

def run(case,n=64,dt=.03,t_end=12.,core=.12,record_every=10):
    cs,gamma,mode=load_source(case,n)
    if len(cs)>4:raise ValueError('max 4 components')
    if dt<=0 or t_end<=0 or core<=0:raise ValueError('invalid parameters')
    steps=int(round(t_end/dt));dt=t_end/steps
    origin=[x.copy() for x in cs]
    H0,self0,_,_=hamiltonian(cs,gamma,core)
    if not np.isfinite(H0) or H0<=0:raise ValueError('nonpositive Hamiltonian proxy')
    out=[];prev_z=None;swaps=0;crossing_times=[];stop_reason=None;stop_t=None
    def snap(k):
        ht,hself,hmut,_=hamiltonian(cs,gamma,core)
        return {'t':round(k*dt,10),'H':ht,'H_self':hself,'H_mutual':hmut,
                'z_centroids':[float(x[:,2].mean()) for x in cs],
                'r_rms':[float(np.sqrt(np.mean(np.sum(x[:,:2]**2,axis=1)))) for x in cs],
                'perimeter':[perimeter(x) for x in cs],
                'vertex_clearance_proxy':clearance_proxy(cs),
                'polygon_segment_clearance':network_segment_clearance(cs)}
    out.append(snap(0))
    prev_z=out[-1]['z_centroids'][0]-out[-1]['z_centroids'][1] if case=='analytic_leapfrog' else None
    for k in range(1,steps+1):
        cs=rk4(cs,gamma,core,dt)
        if not all(np.isfinite(x).all() for x in cs):raise FloatingPointError('nonfinite trajectory')
        if case=='analytic_leapfrog':
            z=float(cs[0][:,2].mean()-cs[1][:,2].mean())
            if z*prev_z<0:swaps+=1;crossing_times.append(k*dt)
            prev_z=z
        if k%record_every==0 or k==steps:
            current=snap(k)
            out.append(current)
            if current['polygon_segment_clearance']<=2*core:
                stop_reason='INTERCOMPONENT_VERTEX_CLEARANCE_CORE_OVERLAP'
            elif abs(current['H']-H0)/abs(H0)>.02:
                stop_reason='REGULARIZED_HAMILTONIAN_DRIFT_GT_2_PERCENT'
            if stop_reason:
                stop_t=k*dt
                break
    H=np.array([x['H'] for x in out]); hs=np.array([x['H_self'] for x in out])
    clearance=min(x['polygon_segment_clearance'] for x in out)
    initial_links=np.array(linking_matrix(origin));final_links=np.array(linking_matrix(cs))
    estimated_integer=np.rint(initial_links)
    max_link_drift=float(np.max(np.abs(final_links-initial_links)))
    max_link_resid=float(np.max(np.abs(initial_links-estimated_integer)))
    energy_drift=float(np.max(np.abs(H-H0))/abs(H0))
    max_self_transfer=float(np.max(np.abs(hs-hs[0]))/abs(H0))
    # Interpretation deliberately limited to discrete filament surrogate.
    # No independent volume-integrated Euler energy-flux measurement.
    gates={
      'G0_source_present':'PASS',
      'G1_native_finite_core_kernel':'PASS' if native_available() else 'DEVELOPMENT_PYTHON_FALLBACK',
      'G2_finite_trajectory':'PASS_FULL_HORIZON' if stop_reason is None else 'STOPPED_PREQUALIFICATION',
      'G3_filament_clearance_proxy':'PASS_SAMPLED_POLYGON_SEGMENTS_ONLY' if clearance>2*core else 'FAIL_PROXY_CORE_OVERLAP',
      'G4_pairwise_linking_proxy':'PASS_PROXY_ONLY' if max_link_drift<.08 and max_link_resid<.08 else 'FAIL_OR_UNRESOLVED',
      'G5_reg_hamiltonian_drift':'PASS_SURROGATE_ONLY' if energy_drift<.02 and stop_reason is None else 'FAIL_OR_EARLY_STOP',
      'G6_analytic_leapfrogging':'PASS_POSITION_SWAP_ONLY' if case=='analytic_leapfrog' and swaps>=2 and stop_reason is None else ('UNRESOLVED_EARLY_STOP' if case=='analytic_leapfrog' else 'NOT_APPLICABLE'),
      'G7_blind_directed_Euler_flux':'NOT_RUN',
      'G8_full_Euler_validation':'NOT_RUN',
      'G9_topology_certification':'NOT_RUN',
      'G10_spatial_temporal_convergence':'NOT_RUN',
      'G11_physical_prediction':'NOT_CLAIMED'
    }
    if case.startswith('borromean'):gates['G9_topology_certification']='UNRESOLVED_MILNOR_TRIPLE_LINK_REQUIRED'
    return {'model':'ROSENHEAD_MIDPOINT_FILAMENT_SURROGATE_NOT_FULL_EULER',
      'case':case,'geometry_mode':mode,'n_per_component':n,'components':len(cs),
      'gamma':gamma,'core_dimensionless':core,'dt':dt,'t_end':t_end,
      'H0':H0,'energy_drift':energy_drift,'self_energy_exchange_proxy':max_self_transfer,
      'stop_reason':stop_reason,'stop_t':stop_t,'completed_horizon':stop_reason is None,
      'minimum_polygon_segment_clearance':clearance,'leapfrog_swaps':swaps,'swap_times':crossing_times,
      'initial_links_proxy':initial_links.tolist(),'final_links_proxy':final_links.tolist(),
      'linking_proxy_max_drift':max_link_drift,'gates':gates,'history':out}

def blind(output:Path,n:int,dt:float,t_end:float,core:float,record_every:int):
    if (output/'LOCK.json').exists() or (output/'SEALED').exists():
        raise FileExistsError(f"Immutable blinded output already exists: {output}; choose a new --out root")
    output.mkdir(parents=True,exist_ok=True);(output/'BLIND').mkdir(exist_ok=True)
    # Cases are assigned random, salted anonymized IDs and run in the resulting frozen order.
    # A separate SEALED directory holds the mapping; BLIND has no case, component, or G6 leak.
    cases=['analytic_leapfrog','trefoil_3_1','torus_2_5','borromean_ideal']
    secret=secrets.token_hex(32)
    rng=random.Random(secret);rng.shuffle(cases)
    commit={f'BX_{sha((secret+case+str(i)).encode())[:12].upper()}':case for i,case in enumerate(cases)}
    lock={'version':'TPDET-v0.1.0','mapping_commit_sha256':sha((json.dumps(commit,sort_keys=True)+secret).encode()),
          'n':n,'dt':dt,'t_end':t_end,'core':core,'record_every':record_every,
          'lock_before_run':True,
          'blind_protocol':'secret randomized mapping; no outcome-dependent tuning; separate SEALED mapping',
          'primary_claim':'NO_FULL_EULER_FLUX_CLAIM'}
    (output/'LOCK.json').write_text(json.dumps(lock,indent=2)+'\n')
    (output/'SEALED').mkdir(exist_ok=True)
    (output/'SEALED/mapping.json').write_text(json.dumps({'secret':secret,'mapping':commit},indent=2)+'\n')
    rows=[]
    for tag,case in commit.items():
        result=run(case,n,dt,t_end,core,record_every)
        result['blind_id']=tag
        # Explicitly redact quantities that identify topology or leak the control.
        for field in ['case','geometry_mode','components','gamma','leapfrog_swaps','swap_times',
                      'initial_links_proxy','final_links_proxy']:
            result.pop(field,None)
        result['gates']['G6_analytic_leapfrogging']='WITHHELD_UNTIL_REVEAL'
        result['gates']['G9_topology_certification']='WITHHELD_UNTIL_REVEAL'
        result['history']=[{k:v for k,v in snapshot.items() if k in
            ('t','H','H_mutual','polygon_segment_clearance')} for snapshot in result['history']]
        (output/'BLIND'/f'{tag}.json').write_text(json.dumps(result,indent=2)+'\n')
        row={k:v for k,v in result.items() if k in ('blind_id','completed_horizon','stop_reason','stop_t',
              'energy_drift','self_energy_exchange_proxy','minimum_polygon_segment_clearance',
              'linking_proxy_max_drift')}
        rows.append(row)
    (output/'BLIND/summary.json').write_text(json.dumps({'lock':lock,'rows':rows,'status':'DEVELOPMENT_ONLY',
       'directed_energy_Euler':'NOT_RUN','not_a_certification':True},indent=2)+'\n')
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='output/TPDET_v0.1.0');p.add_argument('--n',type=int,default=64);p.add_argument('--dt',type=float,default=.03);p.add_argument('--t-end',type=float,default=12.);p.add_argument('--core',type=float,default=.12);p.add_argument('--record-every',type=int,default=10)
    a=p.parse_args(); rows=blind((ROOT/a.out).resolve(),a.n,a.dt,a.t_end,a.core,a.record_every)
    print(json.dumps({'status':'DEVELOPMENT_ONLY','results':rows},indent=2))
if __name__=='__main__':main()
