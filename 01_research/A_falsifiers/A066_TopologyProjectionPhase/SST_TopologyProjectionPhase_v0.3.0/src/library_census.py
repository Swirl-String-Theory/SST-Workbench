"""Independent geometry provider census: no inference about dynamic stability.

Fourier coordinates are provider coefficients; `.short` is a same-provider derived
polyline and cannot close an independent-source gate.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from .topology3d import knot_signature, gauss_link, min_curve_distance
ROOT = Path(__file__).resolve().parents[1]

def hexdigest(b): return hashlib.sha256(b).hexdigest()
def resample(p,n=96):
    p=np.asarray(p,dtype=float)
    if len(p)>1 and np.linalg.norm(p[0]-p[-1])<1e-9:p=p[:-1]
    if len(p)<10:raise ValueError('insufficient source curve samples')
    seg=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    if not np.isfinite(p).all() or seg.min()<1e-12:raise ValueError('nonfinite or zero edge')
    s=np.r_[0,np.cumsum(seg)]
    t=np.arange(n)/n*s[-1]
    return np.column_stack([np.interp(t,s,np.r_[p[:,j],p[0,j]]) for j in range(3)])

def fremlin_coeff(data,n=128):
    lines=[]
    for line in data.decode('utf8',errors='replace').splitlines():
        q=line.strip()
        if not q or q.startswith('%'):continue
        a=q.split()
        if len(a)==3 and all(float(x)==0 for x in a):a=['0']*6
        if len(a)!=6:raise ValueError('Fremlin needs six columns')
        lines.append([float(i) for i in a])
    coef=np.array(lines)
    if coef.ndim!=2 or coef.shape[1]!=6:raise ValueError('wrong Fourier coefficients')
    t=np.arange(n)*2*np.pi/n;harm=np.arange(1,len(coef)+1)
    a=coef[:,[0,2,4]];b=coef[:,[1,3,5]]
    p=np.cos(t[:,None]*harm[None,:])@a+np.sin(t[:,None]*harm[None,:])@b
    return resample(p,n)

def fremlin_short(data,n=96):
    pts=[]
    for line in data.decode('utf8',errors='replace').splitlines():
        q=line.strip()
        if not q or q.startswith('%'):continue
        v=q.split()
        if len(v)!=3:raise ValueError('Fremlin short requires Nx3')
        pts.append([float(x) for x in v])
    return resample(np.array(pts),n)

def ideal_strings(element,n=96):
    curves=[]
    for str_el in element.findall('STRING'):
        coeff=[]
        for r in str_el.findall('Coeff'):
            j=int(r.attrib['I']);a=np.fromstring(r.attrib['A'],sep=',');b=np.fromstring(r.attrib['B'],sep=',')
            if a.shape!=(3,) or b.shape!=(3,):raise ValueError('Bad idealLinks triplet')
            coeff.append((j,a,b))
        ts=np.arange(n)*2*np.pi/n;p=np.zeros((n,3))
        for j,a,b in coeff:
            p+=np.cos(j*ts)[:,None]*a[None,:]+np.sin(j*ts)[:,None]*b[None,:]
        curves.append(resample(p,n))
    return curves

def catalog(root=ROOT):
    path=root/'external_pklsa/source_libraries'
    items=[]
    for fn in sorted(path.rglob('*.fseries')):
        
        try: cc=[fremlin_coeff(fn.read_bytes())]; err=None
        except Exception as exc: cc=[];err=str(exc)
        items.append(dict(id='FS_'+fn.stem.replace('.','_'),provider='fremlin_fseries',source=str(fn.relative_to(root)),sha256=hexdigest(fn.read_bytes()),curves=cc,parse_error=err))
    for fn in sorted(path.rglob('*.short')):
        
        try: cc=[fremlin_short(fn.read_bytes())];err=None
        except Exception as exc:cc=[];err=str(exc)
        items.append(dict(id='SH_'+fn.stem.replace('.','_'),provider='fremlin_short_same_origin',source=str(fn.relative_to(root)),sha256=hexdigest(fn.read_bytes()),curves=cc,parse_error=err))
    txt=(path/'idealLinks.txt').read_text(errors='replace')
    tree=ET.fromstring('<ROOT>'+txt+'</ROOT>')
    for el in tree.findall('.//TL'):
        item_id=el.attrib.get('Id')
        items.append(dict(id='IL_'+item_id,provider='ideal_links',source='external_pklsa/source_libraries/idealLinks.txt#'+item_id,sha256=hexdigest(ET.tostring(el)),curves=ideal_strings(el)))
    fn=root/'external_pklsa/reference/PKLSA_TREFOIL_3_1_N300_CENTERLINE.npz'
    with np.load(fn,allow_pickle=False) as d:p=d['points']
    items.append(dict(id='KP_3_1_N300',provider='knotplot_N300',source=str(fn.relative_to(root)),sha256=hexdigest(fn.read_bytes()),curves=[p]))
    return items

def census(root=ROOT,limit=None):
    items=catalog(root)
    if limit is not None:items=items[:limit]
    results=[]
    for ix,it in enumerate(items):
        row={k:v for k,v in it.items() if k!='curves'}
        row['component_count']=len(it['curves'])
        row['components']=[];row['pair_linking']=[]
        try:
            for c in it['curves']:
                sig=knot_signature(resample(c,96))
                row['components'].append({'status':sig['status'],'alexander_det_m1':sig['alexander_det_at_minus_one'],
                  'projection_crossings':[z.get('crossings') for z in sig['independent_projection_results']]})
            for a in range(len(it['curves'])):
                for b in range(a+1,len(it['curves'])):
                    pa,pb=resample(it['curves'][a],96),resample(it['curves'][b],96)
                    gap=min_curve_distance(pa,pb)
                    v3=gauss_link(pa,pb,3);v5=gauss_link(pa,pb,5)
                    val=round(v5);qualified=gap>1e-6 and abs(v5-val)<.075 and abs(v5-v3)<.075
                    row['pair_linking'].append({'a':a,'b':b,'min_gap':gap,'lk3':v3,'lk5':v5,'integer':val if qualified else None,'status':'QUALIFIED' if qualified else 'UNRESOLVED'})
            row['geometry_status']='SCREENING_COMPLETE' if row['component_count'] and not row.get('parse_error') and all(z['status']=='QUALIFIED' for z in row['components']) and all(z['status']=='QUALIFIED' for z in row['pair_linking']) else 'UNRESOLVED_REFINEMENT'
        except Exception as exc:
            row['geometry_status']='UNRESOLVED_NUMERIC';row['reason']=str(exc)
        row['euler_status']='NOT_RUN_GEOMETRY_CENSUS_ONLY'
        results.append(row)
        if ix%40==0:print(f'geometry census {ix+1}/{len(items)} {it["id"]} : {row["geometry_status"]}',flush=True)
    summary={'total':len(results),'provider_counts':{},'status_counts':{},'n_components':sum(x['component_count'] for x in results),
       'numeric_gate':'three generic projections on 96 point arclength resampling; not a proof of knot type; link q3/q5',
       'independence_rule':'same Fremlin source variants cannot count independent','physical_euler_status':'UNRESOLVED_NOT_TESTED_BY_CENSUS'}
    for r in results:
        summary['provider_counts'][r['provider']]=summary['provider_counts'].get(r['provider'],0)+1
        summary['status_counts'][r['geometry_status']]=summary['status_counts'].get(r['geometry_status'],0)+1
    out=root/'results';out.mkdir(exist_ok=True)
    (out/'GEOMETRY_CENSUS.json').write_text(json.dumps(results,indent=2))
    (out/'GEOMETRY_CENSUS_SUMMARY.json').write_text(json.dumps(summary,indent=2))
    with (out/'GEOMETRY_CENSUS.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['id','provider','source','component_count','geometry_status','alexander_det_m1','linking_integers','reason']);w.writeheader()
        for r in results:w.writerow({k:v for k,v in dict(r,alexander_det_m1=';'.join(str(x['alexander_det_m1']) for x in r['components']),linking_integers=';'.join(str(x['integer']) for x in r['pair_linking'])).items() if k in w.fieldnames})
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int);a=p.parse_args()
    print(json.dumps(census(limit=a.limit),indent=2))
