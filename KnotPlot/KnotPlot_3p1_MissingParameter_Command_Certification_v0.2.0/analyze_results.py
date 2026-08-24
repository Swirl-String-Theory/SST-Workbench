from __future__ import annotations
import argparse,json,hashlib,re,math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
DESIGN=json.loads((ROOT/'matrix_design.json').read_text())

def xyz(path:Path):
    rows=[]
    for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
        s=line.strip()
        if not s or s.startswith(('#','%')): continue
        parts=s.replace(',',' ').split()
        if len(parts)<3: continue
        try: rows.append([float(parts[0]),float(parts[1]),float(parts[2])])
        except ValueError: continue
    a=np.asarray(rows,float)
    if a.ndim!=2 or a.shape[0]<3 or a.shape[1]!=3: raise ValueError(f'not XYZ: {path}')
    return a

def arr_hash(a):
    # geometry hash based on parsed float64 coordinates, not text formatting
    return hashlib.sha256(np.asarray(a,dtype='<f8').tobytes()).hexdigest()

def metrics(a):
    c=a.mean(0); x=a-c
    seg=np.roll(a,-1,axis=0)-a
    L=float(np.linalg.norm(seg,axis=1).sum())
    rg=float(np.sqrt(np.mean(np.sum(x*x,axis=1))))
    u=seg/(np.linalg.norm(seg,axis=1)[:,None]+1e-300)
    dots=np.sum(np.roll(u,1,axis=0)*u,axis=1).clip(-1,1)
    ang=np.arccos(dots)
    return {'n':int(len(a)),'length':L,'rg':rg,'mean_turn':float(ang.mean()),'max_turn':float(ang.max())}

def kabsch_rms(a,b):
    if a.shape!=b.shape:return float('nan')
    A=a-a.mean(0);B=b-b.mean(0)
    H=A.T@B; U,S,Vt=np.linalg.svd(H); R=U@Vt
    if np.linalg.det(R)<0: Vt[-1]*=-1;R=U@Vt
    Ar=A@R
    return float(np.sqrt(np.mean(np.sum((Ar-B)**2,axis=1))))

def audit_status(stage,param,label):
    p=ROOT/'logs'/stage/f'{param}_{label}.audit.json'
    if not p.is_file():return None
    return json.loads(p.read_text())

def analyze_cert():
    (ROOT/'analysis').mkdir(parents=True,exist_ok=True)
    report={'version':'0.2.2','stage':'cert','parameters':{}}
    rows=[]
    for param,cfg in DESIGN['sweeps'].items():
        rec={'values':cfg['values'],'labels':cfg['labels'],'candidates':[]}
        arrays0=[];arrays100=[]; rejected=False; failed=False
        for val,lbl in zip(cfg['values'],cfg['labels']):
            aud=audit_status('cert',param,lbl)
            if not aud or aud['status']=='RUN_FAILED': failed=True
            if aud and aud['status']=='COMMAND_REJECTED': rejected=True
            p0=ROOT/'out/cert'/f'{param}_{lbl}_i00000.txt'; p1=ROOT/'out/cert'/f'{param}_{lbl}_i00100.txt'
            cand={'value':val,'label':lbl,'audit_status':aud['status'] if aud else 'MISSING_AUDIT'}
            if p0.is_file() and p1.is_file():
                a0=xyz(p0);a1=xyz(p1);arrays0.append(a0);arrays100.append(a1)
                cand.update({'i0_hash':arr_hash(a0),'i100_hash':arr_hash(a1),'i0_metrics':metrics(a0),'i100_metrics':metrics(a1)})
            rec['candidates'].append(cand)
        if failed or len(arrays0)!=3:
            status='RUN_FAILED'; common0=False; unique100=0; pair=[]
        else:
            common0=len({arr_hash(a) for a in arrays0})==1
            unique100=len({arr_hash(a) for a in arrays100})
            pair=[]
            for i in range(3):
                for j in range(i+1,3): pair.append({'a':cfg['labels'][i],'b':cfg['labels'][j],'rms':kabsch_rms(arrays100[i],arrays100[j])})
            maxr=max((x['rms'] for x in pair),default=0.0)
            if rejected: status='REJECTED_BY_KNOTPLOT'
            elif not common0: status='INVALID_NONCOMMON_START'
            elif unique100>=2 and maxr>1e-12: status='CERTIFIED_EFFECTIVE'
            else: status='ACCEPTED_NO_EFFECT_AT_100'
        rec.update({'status':status,'common_i0_geometry':common0,'unique_i100_geometries':unique100,'pairwise_i100_aligned_rms':pair})
        report['parameters'][param]=rec
        rows.append((param,status,unique100,max((x['rms'] for x in pair),default=float('nan'))))
    passed=[p for p,r in report['parameters'].items() if r['status']=='CERTIFIED_EFFECTIVE']
    report['certified_effective']=passed
    (ROOT/'analysis/CERTIFICATION.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    md=['# Missing-Parameter Command Certification','', '| parameter | status | unique i100 | max aligned RMS |','|---|---:|---:|---:|']
    for p,s,u,r in rows: md.append(f'| {p} | **{s}** | {u} | {r:.9g} |')
    md+=['',f'Certified for extended stage: **{", ".join(passed) if passed else "NONE"}**','']
    (ROOT/'analysis/CERTIFICATION.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
    print('\n'.join(md)); return 0

def analyze_extended():
    (ROOT/'analysis').mkdir(parents=True,exist_ok=True)
    cert=json.loads((ROOT/'analysis/CERTIFICATION.json').read_text())
    params=cert.get('certified_effective',[])
    report={'version':'0.2.2','stage':'extended','parameters':{}}
    md=['# 1000-iteration Missing-Parameter Sensitivity','']
    for param in params:
        cfg=DESIGN['sweeps'][param]; rr={'candidates':[]}
        final=[]
        for val,lbl in zip(cfg['values'],cfg['labels']):
            p0=ROOT/'out/extended'/f'{param}_{lbl}_i00000.txt'; p100=ROOT/'out/extended'/f'{param}_{lbl}_i00100.txt'; p1000=ROOT/'out/extended'/f'{param}_{lbl}_i01000.txt'
            if not all(p.is_file() for p in [p0,p100,p1000]):
                rr['candidates'].append({'value':val,'label':lbl,'status':'MISSING'}); continue
            a0,a100,a1000=map(xyz,[p0,p100,p1000]); final.append(a1000)
            rr['candidates'].append({'value':val,'label':lbl,'status':'OK','i0':metrics(a0),'i100':metrics(a100),'i1000':metrics(a1000),'i1000_hash':arr_hash(a1000),'rms_i0_to_i1000':kabsch_rms(a0,a1000)})
        rr['unique_i1000_geometries']=len({arr_hash(a) for a in final}) if final else 0
        if len(final)==3:
            rr['min_to_max_i1000_aligned_rms']=kabsch_rms(final[0],final[-1])
        report['parameters'][param]=rr
        md.append(f'## {param}'); md.append(f'- unique i1000 geometries: **{rr["unique_i1000_geometries"]}**')
        if 'min_to_max_i1000_aligned_rms' in rr: md.append(f'- min→max aligned RMS: **{rr["min_to_max_i1000_aligned_rms"]:.9g}**')
        for c in rr['candidates']:
            if c['status']=='OK': md.append(f'- `{c["label"]}` value={c["value"]}: L={c["i1000"]["length"]:.9g}, Rg={c["i1000"]["rg"]:.9g}, maxTurn={c["i1000"]["max_turn"]:.9g}')
        md.append('')
    (ROOT/'analysis/EXTENDED.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (ROOT/'analysis/EXTENDED.md').write_text('\n'.join(md)+'\n',encoding='utf-8'); print('\n'.join(md)); return 0

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--stage',choices=['cert','extended'],required=True); a=ap.parse_args()
    return analyze_cert() if a.stage=='cert' else analyze_extended()
if __name__=='__main__': raise SystemExit(main())
