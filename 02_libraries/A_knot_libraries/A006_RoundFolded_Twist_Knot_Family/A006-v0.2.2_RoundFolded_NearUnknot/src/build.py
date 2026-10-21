"""RoundFolded Near-Unknot v0.2.2 — static seed generator only."""
from pathlib import Path
import sys,argparse,hashlib,json
import numpy as np
from tikz_roundfold import dense_xyz,resample3,EXPECTED,assigned_events,alexander
from near_unknot import PROFILES,annulus_squeeze,params,winding_number_xy,area_vector,toroidal_metrics,approximate_curvature
from knotplot_io import encode,decode
from measure import min_nonlocal,lengths,projection_crossings
ROOT=Path(__file__).resolve().parents[1]

def jsondump(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def recheck_topology(p,label):
    crosses=projection_crossings(p)
    if len(crosses)!=EXPECTED[label][0]:raise ValueError(f'wrong crossings: {label} {len(crosses)}')
    cr=[]
    n=len(p)
    for c in crosses:
        i,j=int(c['segment_a']),int(c['segment_b'])
        vi=p[(i+1)%n]-p[i];vj=p[(j+1)%n]-p[j]
        P=np.array([c['x'],c['y']]);q=P-p[i,:2];w=P-p[j,:2]
        fa=float(np.dot(q,vi[:2])/np.dot(vi[:2],vi[:2]));fb=float(np.dot(w,vj[:2])/np.dot(vj[:2],vj[:2]))
        sign=int(np.sign(np.linalg.det(np.stack((vi[:2],vj[:2])))))
        if sign==0:raise ValueError('degenerate projected crossing')
        dz=float(c['dz'])
        cr.append({'i':i,'j':j,'s':(i+fa)/n,'t':(j+fb)/n,'signed_xy':sign,'dz':dz})
    ev,trace=assigned_events(cr)
    for k,(_,idx,side) in enumerate(ev):
        cc=cr[idx]
        actualOver=(cc['dz']>0) if side=='a' else (cc['dz']<0)
        if actualOver != (k%2==0):
            raise ValueError('Actual lifted over/under disagrees with invariant reconstruction')
    coeff,det=alexander(trace,cr)
    if (coeff,det)!=(EXPECTED[label][1],EXPECTED[label][2]):
        raise ValueError(f'Alexander mismatch {label}: {coeff}, {det}')
    return {'crossings':len(cr),'alexander':coeff,'determinant':int(det),
            'min_abs_crossing_z':float(min(abs(c['dz']) for c in cr)),
            'alternating_lift_verified':True}

def build(label,profile,n):
    P=PROFILES[profile]
    dense,cert=dense_xyz(label)
    center,R,rmin=params(dense)
    out_dense=annulus_squeeze(dense,P['radial_fraction'],P['global_scale'],center,R)
    out=resample3(out_dense,n)*12.0
    top=recheck_topology(out,label)
    m=min_nonlocal(out,neighbor_skip=max(4,int(n*.005)))
    curvature=approximate_curvature(out)
    report_torus=toroidal_metrics(out,center*P['global_scale']*12.0,R*P['global_scale']*12.0)
    if m['distance']<.12: raise RuntimeError('KnotPlot close static gate failed: '+str(m))
    if m['distance']<=2*P['cyl_rad_visual']*1.10:
        raise RuntimeError('Visual tube collision risk; reduce proposed cyl-rad')
    if top['min_abs_crossing_z']<.12:
        raise RuntimeError('Projection crossing lift too small')
    base=f'NearUnknot_{label}_{profile}_N{n:04d}'
    dest=ROOT/'output'/'individual'/base;dest.mkdir(parents=True,exist_ok=True)
    blob=encode([out]);back=decode(blob)[0]
    if not np.array_equal(out,back):raise RuntimeError('KPT roundtrip mismatch')
    (dest/f'{base}.kpt').write_bytes(blob)
    np.savetxt(dest/f'{base}.xyz',out,fmt='%.17g')
    # No unverified KnotPlot parameter-setting syntax is embedded. Use cyl-rad GUI slider.
    (dest/f'{base}_LOAD.kpc').write_text(f'reset all\nshow labels backdrop\n mode cb\n fitto avlength 0.5\n  bradius = 0.2\n cradius = 0.1\n tanf = on\n tanmag = 9\n stusplit = 0\n dstep = 1\n close = 0.20\n max-dr = 0.02\nload output/individual/{base}/{base}.kpt\ninformation\nlength\nparameters cyl-rad\nparameters close\nparameters max-dr\n',encoding='ascii')
    (dest/f'{base}_GO1.kpc').write_text('go 1\n',encoding='ascii')
    (dest/f'{base}_GO32.kpc').write_text('go 32\n',encoding='ascii')
    (dest/f'{base}_SNAPSHOT.kpc').write_text(f'coords output/individual/{base}/{base}_AFTER.xyz\n',encoding='ascii')
    vec=area_vector(out);major=report_torus['major_radius']
    rel=np.array(vec)/(np.pi*major**2)
    report={'release':'0.2.2','status':'DEVELOPMENT_STATIC_CANDIDATE',
        'geometry_source':'v0.2.1 TikZ 14 control points -> periodic cubic spline',
        'source_tikz_equivalence':'UNRESOLVED','label':label,'profile':profile,'n':n,
        'radial_fraction':P['radial_fraction'],'global_scale':P['global_scale'],
        'visual_cyl_rad_suggestion':P['cyl_rad_visual'],'units':'arbitrary KnotPlot coordinates',
        'preserved_analytic_embedding':True,
        'certificates':top,'discrete_nonlocal':m,'length':lengths(out),
        'toroidal_shell':report_torus,'planar_winding':winding_number_xy(out,center*P['global_scale']*12.0),
        'area_vector':vec.tolist(),'impulse_factor_vector_over_matching_ring':rel.tolist(),
        'max_discrete_curvature':float(max(curvature)),
        'estimated_visual_tube_radius_geometry_bound':float(min(.5*m['distance'],1.0/max(curvature))),
        'sha256_kpt':hashlib.sha256(blob).hexdigest(),
        'gates':{'projection_and_alexander':'PASS','KPT_binary_roundtrip':'PASS',
                 'discrete_static_clearance':'PASS','source_to_target_analytic_isotopy':'PASS',
                 'piecewise_linear_isotopy':'NOT_CERTIFIED','KnotPlot_go':'NOT_TESTED',
                 'physical_core_radius':'UNSET','Euler_self_induction':'NOT_TESTED',
                 'toroidal_roll':'UNRESOLVED'}}
    jsondump(dest/'REPORT.json',report)
    # Two separate 0_1 controls: R-matched and filament-length-matched
    for variant, radius in [('R_MATCH',major),('L_MATCH',lengths(out)['total']/(2*np.pi))]:
        ang=2*np.pi*np.arange(n)/n
        circle=np.column_stack((radius*np.cos(ang),radius*np.sin(ang),np.zeros(n)))
        name=f'Unknot_{label}_{profile}_N{n:04d}_{variant}'
        ringdir=ROOT/'output'/'controls'/name;ringdir.mkdir(parents=True,exist_ok=True)
        (ringdir/f'{name}.kpt').write_bytes(encode([circle]))
        np.savetxt(ringdir/f'{name}.xyz',circle,fmt='%.17g')
        (ringdir/f'{name}_LOAD.kpc').write_text(f'reset all\nshow labels backdrop\n mode cb\n fitto avlength 0.5\n  bradius = 0.2\n cradius = 0.1\n tanf = on\n tanmag = 9\n stusplit = 0\n dstep = 1\n close = 0.20\n max-dr = 0.02\nload output/controls/{name}/{name}.kpt\ninformation\nlength\n',encoding='ascii')
    print(f'{label:3s} {profile:11s} N={n:4d} min={m["distance"]:.4f} shell/R={report_torus["minor_to_major"]:.4f} winding={report["planar_winding"]} I_z/I0={rel[2]:+.6f}')
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('mode',nargs='?',default='BASIC',choices=['SMOKE','BASIC','FULL','ALL'])
    ap.add_argument('--profiles',nargs='+',choices=list(PROFILES),default=list(PROFILES))
    opts=ap.parse_args()
    if opts.mode=='ALL': ns=[256,512,1024]
    else:ns=[{'SMOKE':256,'BASIC':512,'FULL':1024}[opts.mode]]
    records=[build(k,p,n) for n in ns for p in opts.profiles for k in ['5_2','6_1']]
    jsondump(ROOT/'LATEST_BUILD.json',{'version':'0.2.2','run_mode':opts.mode,'static_gates':'PASS',
            'count':len(records),'cases':[{'label':x['label'],'profile':x['profile'],'n':x['n']} for x in records],
            'physical_status':'NOT_TESTED','topology_during_knotplot_relaxation':'UNRESOLVED'})

if __name__=='__main__':main()