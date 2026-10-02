from __future__ import annotations
import csv, json, math, hashlib, sys
from pathlib import Path
from collections import defaultdict

ROOT=Path(__file__).resolve().parent

def xyz(path):
    pts=[]
    for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
        a=line.split()
        if len(a)<3: continue
        try: pts.append(tuple(map(float,a[:3])))
        except ValueError: pass
    if len(pts)<4: raise ValueError(f'too few XYZ points: {path}')
    return pts

def dist(a,b): return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))
def metrics(path):
    p=xyz(path); n=len(p)
    L=sum(dist(p[i],p[(i+1)%n]) for i in range(n))
    c=tuple(sum(q[k] for q in p)/n for k in range(3))
    rg=math.sqrt(sum(sum((q[k]-c[k])**2 for k in range(3)) for q in p)/n)
    ext=[max(q[k] for q in p)-min(q[k] for q in p) for k in range(3)]
    minnon=float('inf')
    skip=max(2,min(6,n//20))
    for i in range(n):
        for j in range(i+1,n):
            sep=min(j-i,n-(j-i))
            if sep<=skip: continue
            d=dist(p[i],p[j])
            if d<minnon: minnon=d
    turns=[]
    for i in range(n):
        a=p[i-1]; b=p[i]; c2=p[(i+1)%n]
        u=tuple(b[k]-a[k] for k in range(3)); v=tuple(c2[k]-b[k] for k in range(3))
        nu=math.sqrt(sum(x*x for x in u)); nv=math.sqrt(sum(x*x for x in v))
        if nu and nv:
            co=max(-1,min(1,sum(u[k]*v[k] for k in range(3))/(nu*nv))); turns.append(math.acos(co))
    thickness=.5*minnon if math.isfinite(minnon) else float('nan')
    return {'n_points':n,'length':L,'rg':rg,'bbox_x':ext[0],'bbox_y':ext[1],'bbox_z':ext[2],'min_nonlocal_point_distance':minnon,'thickness_proxy':thickness,'ropelength_proxy':L/thickness if thickness>0 else None,'turn_mean':sum(turns)/len(turns),'turn_max':max(turns),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def fatal_logs():
    bad={}
    for p in sorted((ROOT/'logs').glob('*_audit.json')):
        d=json.loads(p.read_text())
        if d.get('status')!='PASS': bad[p.name]=d
    # If no audit JSON exists but old console logs do, treat legacy marker-containing logs as invalid.
    if not list((ROOT/'logs').glob('*_audit.json')):
        for p in sorted((ROOT/'logs').glob('*_console.log')):
            t=p.read_text(errors='replace').lower()
            marks=[m for m in ('unknown command','this command is obsolete',"can't open file") if m in t]
            if marks: bad[p.name]={'legacy_log_markers':marks}
    return bad

def main(argv=None):
    allow='--allow-invalid' in (argv or sys.argv[1:])
    bad=fatal_logs()
    if bad and not allow:
        print('ERROR: matrix logs are invalid/stale. Run run_fresh_discovery.cmd first.')
        print(json.dumps(bad,indent=2)[:8000]); return 2
    design=json.loads((ROOT/'matrix_design.json').read_text())
    out=ROOT/'out'; analysis=ROOT/'analysis'; analysis.mkdir(exist_ok=True)
    rows=[]; missing=[]
    final_hash=defaultdict(list)
    for e in design['entries']:
        cid=e['candidate']
        # anneal has nonstandard intermediate names; analyze final only plus q60 i00000.
        if cid=='A90_anneal_q0': cps=[('i00000','A90_anneal_q60_i00000'),('i10000','A90_anneal_q0_i10000')]
        else: cps=[(cp,f'{cid}_{cp}') for cp in e['checkpoints']]
        for cp,stem in cps:
            f=out/f'{stem}.txt'
            if not f.is_file(): missing.append(str(f)); continue
            m=metrics(f); r={'candidate':cid,'family':e['family'],'swept_variable':e['swept_variable'],'swept_value':e['swept_value'],'checkpoint':cp,**m}; rows.append(r)
            if cp=='i10000': final_hash[m['sha256']].append(cid)
    fields=['candidate','family','swept_variable','swept_value','checkpoint','n_points','length','rg','bbox_x','bbox_y','bbox_z','min_nonlocal_point_distance','thickness_proxy','ropelength_proxy','turn_mean','turn_max','sha256']
    with (analysis/'matrix_metrics.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    fam=defaultdict(list)
    finals={r['candidate']:r for r in rows if r['checkpoint']=='i10000'}
    initials={r['candidate']:r for r in rows if r['checkpoint']=='i00000'}
    for e in design['entries']:
        cid=e['candidate']; f=finals.get(cid); i=initials.get(cid)
        if not f: continue
        item={'candidate':cid,'value':e['swept_value'],'final':f}
        if i: item['delta']={k:f[k]-i[k] for k in ('length','rg','ropelength_proxy','turn_mean') if f.get(k) is not None and i.get(k) is not None}
        fam[e['family']].append(item)
    flags=[]
    for family,items in fam.items():
        if len(items)>=2:
            hashes={x['final']['sha256'] for x in items}
            if len(hashes)==1: flags.append({'family':family,'flag':'ALL_FINAL_GEOMETRIES_BYTE_IDENTICAL','n':len(items)})
    dup=[{'sha256':h,'candidates':v} for h,v in final_hash.items() if len(v)>1]
    report={'schema_version':1,'valid_logs':not bool(bad),'missing_files':missing,'n_rows':len(rows),'n_final_candidates':len(finals),'n_unique_final_byte_hashes':len(final_hash),'duplicate_groups':dup,'family_flags':flags,'families':fam}
    (analysis/'matrix_analysis.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    lines=['# Matrix effect report','',f"Final candidates: **{len(finals)}**; unique byte geometries: **{len(final_hash)}**.",'']
    if missing: lines += [f'⚠ Missing expected files: {len(missing)}','']
    if flags:
        lines += ['## Red flags','']+[f"- **{x['family']}**: {x['n']} final geometries are byte-identical; check whether the swept setting was actually applied." for x in flags]+['']
    lines += ['## Family table','']
    for family,items in fam.items():
        lines += [f'### {family}','', '| candidate | value | length | Rg | ropelength proxy | final SHA prefix |','|---|---:|---:|---:|---:|---|']
        for x in items:
            z=x['final']; lines.append(f"| {x['candidate']} | {x['value']} | {z['length']:.8g} | {z['rg']:.8g} | {z['ropelength_proxy']:.8g} | {z['sha256'][:12]} |")
        lines.append('')
    (analysis/'MATRIX_EFFECTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f"Wrote {analysis/'matrix_metrics.csv'}")
    print(f"Wrote {analysis/'MATRIX_EFFECTS.md'}")
    print(f"Final candidates={len(finals)}, unique byte geometries={len(final_hash)}")
    return 0 if not missing else 4
if __name__=='__main__': raise SystemExit(main())
