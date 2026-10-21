#!/usr/bin/env python3
"""RoundFolded Twist Knot Family v0.2.0 DEVELOPMENT build.
Static 4-plat projections and Borromean local-connected-sum candidates only.
No physics certification, no KnotPlot runtime execution.
"""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from roundfold import fourplat,resample_closed,name,fox_determinant,alexander_coefficients,expected_alexander
from knotplot_io import encode,decode
from measure import projection_crossings,lengths,min_nonlocal
from borromean import make as make_borromean
ROOT=Path(__file__).resolve().parents[1]

def sha(data):return hashlib.sha256(data).hexdigest()
def write_json(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def kpc_scripts(folder,base,relative):
    """Scripts are separate: no asynchronous go followed by an immediate snapshot."""
    scripts={
        'LOAD':f'reset all\nload {relative}\ninformation\nlength\n',
        'GO1':f'go 1\n',
        'GO32':f'go 32\n',
        'SNAPSHOT':f'coords {folder.relative_to(ROOT).as_posix()}/{base}_AFTER.xyz\n',
    }
    for k,body in scripts.items():
        (folder/f'{base}_{k}.kpc').write_text(body,encoding='ascii')

def save_geometry(case,comps,report,section):
    dest=ROOT/'output'/section/case
    dest.mkdir(parents=True,exist_ok=True)
    blob=encode(comps);got=decode(blob)
    if len(comps)!=len(got) or not all(np.array_equal(a,c) for a,c in zip(comps,got)):
        raise ValueError('KPT roundtrip unequal')
    kpt=dest/(case+'.kpt');kpt.write_bytes(blob)
    for i,p in enumerate(comps):
        np.savetxt(dest/f'component_{i}.xyz',p,fmt='%.17g')
    report['output_sha256']=sha(blob)
    write_json(dest/'REPORT.json',report)
    rel=kpt.relative_to(ROOT).as_posix();kpc_scripts(dest,case,rel)
    return {'case':case,'status':report['status'],'min_clearance':report.get('minimum_nonlocal_self_clearance',None)}

def individual(m,n,scale=2.0,handedness='original'):
    raw,diagram=fourplat(m)
    if handedness=='mirror': raw[:,2]*=-1
    p=resample_closed(raw,n)*scale
    if (np.linalg.norm(np.diff(p,axis=0),axis=1)<1e-9).any():raise ValueError('zero edge')
    crossings=projection_crossings(p)
    D=fox_determinant(diagram['traversal'],m+2)
    a=alexander_coefficients(diagram)
    target=expected_alexander(m)
    if len(crossings)!=m+2 or D!=2*m+1 or a!=target:
        raise ValueError('projection, Alexander or determinant topological gate failed')
    stat=lengths(p)
    sep=min_nonlocal(p,neighbor_skip=max(5,int(.004*n)))
    if not np.isfinite(sep['distance']) or sep['distance']<0.12:
        raise ValueError(f'unsafe segment clearance {sep} for {m}')
    crossing_gap=min(abs(x['dz']) for x in crossings)
    if crossing_gap<0.20:raise ValueError('crossing lift too small')
    case=f'Tm{m}_{name(m)}_{handedness}_N{n:04d}'
    report={'schema':'SST-ROUND-FOLDED-2','version':'0.2.0','case':case,'status':'STATIC_CANDIDATE',
            'geometry_method':'projection_first_plat_closure_round_annular_diffeomorphism',
            'source_family':'generated_4_plat_not_KnotPlot_relaxed',
            'm':m,'knot_label_intended':name(m),'conway_convention':f'[{m},2]',
            'braid_word':diagram['word'],'writhe_convention':'mirror corresponds to z reversal',
            'diagram_crossings':m+2,'observed_projection_crossings':len(crossings),
            'minimum_projected_crossing_dz':crossing_gap,
            'alexander_polynomial_ascending':a,'expected_alexander':target,
            'fox_determinant':D,'expected_determinant':2*m+1,
            'metrics':stat,'minimum_nonlocal_self_clearance':sep,
            'physical_units':'dimensionless KnotPlot coordinates',
            'gates':{'parametric_diagram':'PASS','wirtinger_alexander':'PASS',
                     'projection_crossing_count':'PASS','kpt_byte_roundtrip':'PASS',
                     'geometric_clearance_screen':'PASS',
                     'ambient_isotopy_independent':'UNRESOLVED','knotplot_runtime_go':'NOT_TESTED',
                     'Euler_PKLSA_dynamics':'NOT_TESTED'}}
    return save_geometry(case,[p],report,'individual')

def borromean(ms,n,scale=10.0):
    cs,d=make_borromean(ms,n=n,scale=scale)
    lo=min(d['intercomponent_segment_clearance'].values());si=min(d['self_segment_clearance_screen'])
    if not np.isfinite(lo) or lo<0.12 or si<0.12:raise ValueError(f'Borromean clearance failed: inter={lo},self={si}')
    if max(abs(v) for v in d['pairwise_linking_numerical'].values())>.03:raise ValueError('pairwise linking not zero')
    case='Borromean_'+'_'.join(name(m) for m in ms)+f'_N{n:04d}'
    report={'schema':'SST-ROUND-FOLDED-2','version':'0.2.0','case':case,
            'status':'STATIC_CANDIDATE_TOPOLOGY_UNRESOLVED',
            'construction':'3-braid Borromean skeleton plus local connected-sum candidates',
            'component_labels_intended':[name(m) for m in ms],
            'minimum_nonlocal_self_clearance':min(d['self_segment_clearance_screen']),
            'minimum_intercomponent_clearance':min(d['intercomponent_segment_clearance'].values()),
            'input_4_plat_word_by_component':[[(int(k),int(s)) for k,s in __import__('roundfold').word(m)] for m in ms],
            'metrics':[lengths(p) for p in cs],'borromean_diagnostics':d,
            'gates':{'borromean_braid_word':'PASS','pairwise_gauss_linking_zero':'PASS_NUMERIC',
                     'intercomponent_clearance':'PASS_SCREEN','intrastrand_clearance':'PASS_SCREEN',
                     'local_connected_sum_embedding':'UNRESOLVED',
                     'component_knot_polynomials':'UNRESOLVED',
                     'Milnor_mu123':'UNRESOLVED','knotplot_runtime_go':'NOT_TESTED',
                     'Euler_PKLSA_dynamics':'NOT_TESTED'}}
    return save_geometry(case,cs,report,'borromean')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=['ALL','INDIVIDUAL','BORROMEAN'],default='ALL')
    ap.add_argument('--m',type=int,nargs='*',default=[3,4,5,6]);ap.add_argument('--borromean-m',type=int,nargs=3,default=[3,3,4]);
    ap.add_argument('--n',type=int,default=1024);ap.add_argument('--borromean-n',type=int,default=768)
    ap.add_argument('--scale',type=float,default=2.0)
    a=ap.parse_args()
    if any(x<1 for x in a.m+a.borromean_m):ap.error('m>=1 required')
    if a.n<256 or a.borromean_n<256:ap.error('n>=256 required')
    done=[]
    if a.mode in ('ALL','INDIVIDUAL'):
        for m in a.m: done.append(individual(m,n=a.n,scale=a.scale))
    if a.mode in ('ALL','BORROMEAN'):
        done.append(borromean(a.borromean_m,n=a.borromean_n))
    write_json(ROOT/'LATEST_BUILD.json',{'version':'0.2.0','status':'DEVELOPMENT','items':done,'certified_Euler':False,'certified_topology_borromean':False})
    print(json.dumps({'status':'DEVELOPMENT_STATIC_ONLY','items':done},indent=2))

if __name__=='__main__':main()
