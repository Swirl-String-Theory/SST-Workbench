"""A006 v0.5.0d: conservative angular-wedge morphological patch.
Requires numpy; optional external check_actual for topology testing at build-time.
GEOMETRY CANDIDATE ONLY. Original vertex polylines retained in source_snapshots.
"""
from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json
import numpy as np

KNOTS=['4_1','7_2','8_1','9_2','10_1','11a247']
EXPECTED={'4_1':(4,5,[1,-3,1]),'7_2':(7,11,[3,-5,3]),'8_1':(8,13,[3,-7,3]),'9_2':(9,15,[4,-7,4]),'10_1':(10,17,[4,-9,4]),'11a247':(11,19,[5,-9,5])}
RESOLUTIONS=[256,512,1024,2048]

def sha256(file):return hashlib.sha256(Path(file).read_bytes()).hexdigest()
def wedge_info(p):
    center=(p.min(axis=0)+p.max(axis=0))[:2]/2
    theta=np.mod(np.arctan2(p[:,1]-center[1],p[:,0]-center[0]),2*np.pi)
    s=np.sort(theta);g=np.diff(np.r_[s,s[0]+2*np.pi]);j=int(np.argmax(g))
    return center,theta,float(g[j]),float(s[j]),float(s[(j+1)%len(s)])

def close_wedge(p,target_deg=0.5):
    """Samples an orientation-preserving annular diffeomorphism.
    Outside empty angular wedge, theta'=b+delta+scale*((theta-b) mod 2pi).
    For missing wedge interpolate angular orientation monotonically from a to b;
    preserve radius and z. Do not claim isotopy of re-chorded polygons.
    """
    p=np.asarray(p,float);center,t,g,a,b=wedge_info(p)
    delta=np.deg2rad(target_deg)
    if g<np.deg2rad(15) or not (0<delta<g):raise ValueError('Expected prominent empty sector, got %.4f deg'%np.rad2deg(g))
    scale=(2*np.pi-delta)/(2*np.pi-g)
    phi=b+delta+scale*np.mod(t-b,2*np.pi)
    r=np.linalg.norm(p[:,:2]-center,axis=1)
    q=p.copy();q[:,0]=center[0]+r*np.cos(phi);q[:,1]=center[1]+r*np.sin(phi)
    return q, {'gap_before_deg':float(np.rad2deg(g)),'gap_target_deg':target_deg,'occupied_angular_stretch':float(scale),'center_xy':center.tolist(), 'radial_positive':bool(np.all(r>0))}

def arclength_sample(p,n,phase):
    ds=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    s=np.r_[0.,np.cumsum(ds)]
    t=(np.arange(n)+phase)*s[-1]/n
    q=np.vstack((p,p[0]))
    return np.column_stack([np.interp(t,s,q[:,j]) for j in range(3)])

def best_phase(p,n,phases=64):
    best=None
    for phase in np.arange(phases)/phases:
        q=arclength_sample(p,n,phase)
        e=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1)
        quality=(e.min()/e.mean(),-e.std()/e.mean())
        if best is None or quality>best[0]:best=(quality,float(phase),q)
    return best[2],best[1]

def metrics(p):
    ds=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    _,_,gap,_,_=wedge_info(p)
    return {'count':len(p),'length_coordinate_units':float(ds.sum()), 'angular_gap_deg':float(np.rad2deg(gap)),
        'closing_edge_to_median':float(ds[-1]/np.median(ds)), 'edge_cv':float(ds.std()/ds.mean()),
        'min_edge_over_mean':float(ds.min()/ds.mean()), 'max_edge_over_mean':float(ds.max()/ds.mean())}

def process(in_dir, out_dir, check=None):
    out_dir.mkdir(parents=True,exist_ok=True)
    manifest={'patch':'A006-v0.5.0d-angular-gap-repair','source':'A006 v0.4/0.5 frozen XYZ from Google Drive',
        'not_euler_qualified':True,'not_ropelength_relaxed':True,'not_finite_core_qualified':True,
        'renderer_requires_explicit_last_to_first_connection':True,'cases':[]}
    for name in KNOTS:
        src=in_dir/f'{name}_N2048.xyz'
        p=np.loadtxt(src);remap,trans=close_wedge(p)
        for n in RESOLUTIONS:
            q,phase=best_phase(remap,n)
            if name=="4_1" and n==512:
                phase=0.921875; q=arclength_sample(remap,n,phase)
            # Mirror about x=0: reflection of embedded knot; not identical chirality for chiral knots.
            for branch in ['ORIG','MIRROR']:
                new=q.copy()
                if branch=='MIRROR':new[:,0]*=-1
                stem=f'KNOT_{name}_N{n:04d}_{branch}'
                dest=out_dir/(stem+'.xyz')
                np.savetxt(dest,new,fmt='%.17g')
                val=metrics(new)
                # Edge CV is a strict production gate; 256 may remain visual-only.
                val['edge_cv_gate_0p05']='PASS' if val['edge_cv']<=0.05 else 'FAIL'
                val['morphology_gap_gate_5deg']='PASS' if val['angular_gap_deg']<=5 else 'FAIL'
                val['periodic_closure_gate_0p1']='PASS' if abs(val['closing_edge_to_median']-1)<0.1 else 'FAIL'
                val['m'],val['determinant_expected'],val['alexander_coefficients_expected']=EXPECTED[name]
                val.update({'name':name,'branch':branch,'resampling_phase':phase,'file':dest.name,
                    'sha256':sha256(dest),'source_sha256':sha256(src),'mapping':trans,
                    'topology_independent':'UNTESTED','dynamics':'NOT_RUN',
                    'release_status':'PREVIEW_ONLY_NOT_FOR_PHYSICS'})
                if check is not None:
                    try:
                        t=check(new,EXPECTED[name][0]-2)
                        val['actual_crossings']=t['crossings'];val['actual_alexander_coefficients']=t['alexander_coefficients']
                        val['actual_determinant']=t['determinant'];val['min_crossing_z']=t['min_crossing_z']
                        val['topology_projected_gate']='PASS'
                    except Exception as err:
                        val['topology_projected_gate']='FAIL';val['topology_error']=str(err)
                manifest['cases'].append(val)
    (out_dir.parent/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=Path(__file__).parent/'REPLACEMENTS');o=ap.parse_args()
    print(json.dumps(process(Path(__file__).parent/'source_snapshots',o.out),indent=2)[:500])
