#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, os, re, subprocess, sys
from pathlib import Path


def loadj(p: Path): return json.loads(p.read_text(encoding='utf-8'))
def dumpj(p: Path, o): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(o, indent=2, sort_keys=True)+'\n', encoding='utf-8')
def sha(p: Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024), b''): h.update(b)
    return h.hexdigest()

def norm(x):
    s=str(x or '').strip().lower().replace(' ','').replace('-','_').replace('.','_')
    m={'trefoil':'3_1','k3_1':'3_1','figure8':'4_1','figure_eight':'4_1','k4_1':'4_1',
       'k5_1':'5_1','k5_2':'5_2','k6_1':'6_1','k6_2':'6_2','unknot':'0_1','circle':'0_1',
       'hopf':'l2a1','hopf_link':'l2a1','solomon':'l4a1','solomon_link':'l4a1',
       'borromean':'l6a4','borromean_rings':'l6a4','2a1':'l2a1','4a1':'l4a1','6a4':'l6a4'}
    s=m.get(s,s)
    return 'L'+s[1:] if re.fullmatch(r'l\d+a\d+',s) else s

TOPO_KEYS=('topology','topology_id','topology_name','canonical_topology','knot','knot_id','link','link_id','family','expected_topology')
ID_KEYS=('carrier_id','candidate_id','geometry_id','id','seed_id','blind_candidate_id','record_id')
GROUP_KEYS=('independence_group','independence_family','source_independence_group','source_family','provider','provenance_family','representation_family')

def first(d, keys):
    for k in keys:
        v=d.get(k)
        if v not in (None,'',[]): return v
    return None

def nested_first(row, keys):
    v=first(row,keys)
    if v is not None: return v
    for nk in ('identity','topology_metadata','metadata','source','provenance'):
        sub=row.get(nk)
        if isinstance(sub,dict):
            v=first(sub,keys)
            if v is not None: return v
    return None

def row_topology(r): return norm(nested_first(r,TOPO_KEYS))
def row_id(r,i):
    v=nested_first(r,ID_KEYS)
    if v is not None: return str(v)
    b=json.dumps(r,sort_keys=True,separators=(',',':')).encode(); return f'row-{i:06d}-{hashlib.sha256(b).hexdigest()[:12]}'
def row_group(r): return str(nested_first(r,GROUP_KEYS) or 'UNKNOWN')
def bad(r):
    for k in ('status','qualification_status','literature_gate_status','hard_gate_status'):
        if isinstance(r.get(k),str) and r[k].strip().lower() in {'fail','failed','rejected','excluded','invalid'}: return True
    return any(r.get(k) is True for k in ('duplicate','is_duplicate','byte_identical_duplicate','excluded'))

def find_one(root:Path, pattern:str):
    hits=sorted(root.glob(pattern), key=lambda p:(len(p.parts),str(p).lower()))
    if not hits: raise FileNotFoundError(f'No {pattern!r} under {root}')
    return hits[0]

def jsonl(p):
    out=[]
    for n,line in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
        if not line.strip(): continue
        x=json.loads(line)
        if isinstance(x,dict): out.append(x)
    return out

def active_topos(tc,profile):
    p='FULL' if profile=='PLAN' else profile
    return [x for x in tc['topologies'] if p in x.get('profiles',[])]

def build_manifest(pklsa,cfg,tc,profile,out):
    metrics=find_one(pklsa,cfg['pklsa']['geometry_metrics_glob'])
    rows=jsonl(metrics); per=cfg['carriers_per_topology']['FULL' if profile=='PLAN' else profile]
    idx={}
    for i,r in enumerate(rows):
        if bad(r): continue
        t=row_topology(r)
        if t: idx.setdefault(t,[]).append((i,r))
    selected=[]; missing=[]
    for spec in active_topos(tc,profile):
        aliases={norm(a) for a in spec.get('aliases',[])}|{norm(spec['id'])}
        pool=[]
        for a in aliases: pool += idx.get(a,[])
        uniq={}
        for i,r in pool: uniq.setdefault(row_id(r,i),(i,r,row_group(r)))
        vals=sorted([(i,r,cid,g) for cid,(i,r,g) in uniq.items()], key=lambda x:(x[3]=='UNKNOWN',x[3],x[2]))
        chosen=[]; groups=set()
        for x in vals:
            if x[3]!='UNKNOWN' and x[3] in groups: continue
            chosen.append(x); groups.add(x[3])
            if len(chosen)>=per: break
        if len(chosen)<per:
            ids={x[2] for x in chosen}
            for x in vals:
                if x[2] in ids: continue
                chosen.append(x)
                if len(chosen)>=per: break
        if len(chosen)<per:
            missing.append({'topology':spec['id'],'required':per,'found':len(chosen),'aliases':sorted(aliases)}); continue
        for i,r,cid,g in chosen:
            selected.append({'topology':spec['id'],'class':spec.get('class'),'roles':spec.get('roles',[]),'carrier_id':cid,
                             'independence_group':g,'geometry_metrics_row_sha256':hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                             'geometry_metrics_row':r})
    if missing: raise RuntimeError('Insufficient qualified PKLSA carriers:\n'+json.dumps(missing,indent=2))
    m={'schema':'SST-CROSS-CARRIER-MANIFEST-1','pklsa_release_id':cfg['pklsa']['release_id'],'profile':profile,
       'geometry_metrics_path':str(metrics),'geometry_metrics_sha256':sha(metrics),'carriers_per_topology':per,
       'selected_topologies':[x['id'] for x in active_topos(tc,profile)],'carrier_count':len(selected),'carriers':selected}
    m['self_content_sha256_without_self_field']=hashlib.sha256(json.dumps(m,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    dumpj(out,m); return m

def eligible_contract(c,req,release):
    if c.get('schema')!=req['schema']: return False,'schema mismatch'
    if c.get('input_geometry_source')!=req['input_geometry_source']: return False,'not bound to common PKLSA carrier manifest'
    if c.get('forbid_legacy_outputs') is not True: return False,'legacy outputs not forbidden'
    if c.get('pklsa_required') is not True: return False,'pklsa_required != true'
    if c.get('enabled') is False: return False,'disabled'
    a=c.get('accepted_pklsa_release_ids',[])
    if a and release not in a: return False,f'{release} not accepted'
    if not isinstance(c.get('run'),dict) or not c['run'].get('command'): return False,'missing run command'
    return True,'eligible'

def render(x,m): return str(x).format(**m)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--profile',required=True,choices=['PLAN','BASIC','FULL','CERTIFY']); ap.add_argument('--workbench-root',required=True); ap.add_argument('--campaign-config',required=True); ap.add_argument('--topology-manifest',required=True); a=ap.parse_args()
    wb=Path(a.workbench_root).resolve(); cfgp=Path(a.campaign_config).resolve(); tpp=Path(a.topology_manifest).resolve(); cfg=loadj(cfgp); tc=loadj(tpp)
    pk=wb/cfg['pklsa']['release_root_rel']
    if not pk.exists(): print(f'[ERROR] Missing PKLSA root: {pk}',file=sys.stderr); return 2
    rfiles=[]
    for rel in cfg['pklsa']['required_release_files']:
        p=pk/rel
        if not p.exists(): print(f'[ERROR] Missing PKLSA release file: {p}',file=sys.stderr); return 2
        rfiles.append(p)
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ'); cid=f"{cfg['campaign_id_prefix']}-{a.profile}-{stamp}"; out=wb/cfg['output_root_rel']/cid; out.mkdir(parents=True,exist_ok=False)
    dumpj(out/'CROSS_PROTOCOL_FREEZE.json',{'schema':'SST-CROSS-PROTOCOL-FREEZE-1','campaign_id':cid,'profile':a.profile,'campaign_config_sha256':sha(cfgp),'topology_manifest_sha256':sha(tpp),'pklsa_release_id':cfg['pklsa']['release_id'],'pklsa_release_files':[{'path':str(p),'sha256':sha(p)} for p in rfiles],'legacy_results_allowed_as_evidence':False})
    try: cm=build_manifest(pk,cfg,tc,a.profile,out/'CROSS_CARRIER_MANIFEST.json')
    except Exception as e:
        dumpj(out/'CROSS_RUN_SUMMARY.json',{'campaign_id':cid,'status':'INFRASTRUCTURE_FAIL','error':str(e)}); print(f'[ERROR] {e}',file=sys.stderr); return 2
    elig=[]; rej=[]
    for cp in sorted(wb.glob(cfg['member_contract_glob'])):
        try: c=loadj(cp)
        except Exception as e: rej.append({'path':str(cp),'contract':{},'reason':f'invalid json: {e}'}); continue
        ok,why=eligible_contract(c,cfg['required_contract'],cfg['pklsa']['release_id']); (elig if ok else rej).append({'path':str(cp),'contract':c,'reason':why})
    elig.sort(key=lambda x:(int(x['contract'].get('stage',9999)),x['contract'].get('catalog_id',''),x['contract'].get('version','')))
    dumpj(out/'MEMBER_DISCOVERY.json',{'schema':'SST-CROSS-MEMBER-DISCOVERY-1','campaign_id':cid,
      'eligible':[{'path':x['path'],'catalog_id':x['contract'].get('catalog_id'),'version':x['contract'].get('version'),'stage':x['contract'].get('stage')} for x in elig],
      'rejected':[{'path':x['path'],'catalog_id':x['contract'].get('catalog_id'),'version':x['contract'].get('version'),'reason':x['reason']} for x in rej]})
    print(f'[E011] Campaign         : {cid}'); print(f'[E011] PKLSA release    : {cfg["pklsa"]["release_id"]}'); print(f'[E011] Carrier count    : {cm["carrier_count"]}'); print(f'[E011] Eligible members : {len(elig)}'); print(f'[E011] Output root      : {out}')
    if a.profile=='PLAN':
        for x in elig: print(f"  ELIGIBLE stage={x['contract'].get('stage')} {x['contract'].get('catalog_id')} {x['contract'].get('version')} :: {x['path']}")
        for x in rej: print(f"  REJECTED {x['contract'].get('catalog_id','?')} {x['contract'].get('version','?')} :: {x['reason']} :: {x['path']}")
        return 0
    if not elig: print('[ERROR] No eligible cross-falsifier members found.',file=sys.stderr); return 3
    env=os.environ.copy(); env.update({'SST_CROSS_FALSIFIER':'1','SST_DISABLE_LEGACY_RESULTS':'1','SST_CROSS_REQUIRE_PKLSA':'1','SST_CROSS_CAMPAIGN_ID':cid,'SST_CROSS_CARRIER_MANIFEST':str(out/'CROSS_CARRIER_MANIFEST.json'),'SST_PKLSA_RELEASE_ROOT':str(pk),'SST_CROSS_OUTPUT_ROOT':str(out/'members')}); env.setdefault('SST_NATIVE_THREADS',str(cfg['runtime']['native_threads_default']))
    results=[]; errors=0
    for x in elig:
        c=x['contract']; cp=Path(x['path']); wd=(cp.parent/c['run'].get('working_directory','.')).resolve(); mp={'profile':a.profile,'workbench_root':str(wb),'campaign_id':cid,'carrier_manifest':str(out/'CROSS_CARRIER_MANIFEST.json'),'cross_output_root':str(out/'members'),'pklsa_release_root':str(pk)}; command=render(c['run']['command'],mp); args=[render(v,mp) for v in c['run'].get('args',[])]
        logdir=out/'logs'; logdir.mkdir(exist_ok=True); log=logdir/f"{c.get('catalog_id','UNKNOWN')}_{c.get('version','UNKNOWN')}.log"
        if os.name=='nt' and command.lower().endswith(('.cmd','.bat')): argv=['cmd.exe','/d','/s','/c','call',command,*args]
        else: argv=[command,*args]
        print(f"[E011] RUN stage={c.get('stage')} {c.get('catalog_id')} {c.get('version')}")
        if not wd.exists(): rc=9009; log.write_text(f'Working directory missing: {wd}\n',encoding='utf-8')
        else:
            with log.open('w',encoding='utf-8',errors='replace') as f: rc=subprocess.run(argv,cwd=wd,env=env,stdout=f,stderr=subprocess.STDOUT,text=True,shell=False).returncode
        status='COMPLETED' if rc==0 else 'RUNTIME_ERROR'; errors += (rc!=0); results.append({'catalog_id':c.get('catalog_id'),'version':c.get('version'),'stage':c.get('stage'),'status':status,'returncode':rc,'contract_path':str(cp),'log_path':str(log)})
        if rc!=0 and not cfg['runtime'].get('continue_after_child_runtime_error',True): break
    dumpj(out/'CROSS_RUN_SUMMARY.json',{'schema':'SST-CROSS-RUN-SUMMARY-1','campaign_id':cid,'profile':a.profile,'pklsa_release_id':cfg['pklsa']['release_id'],'legacy_results_allowed_as_evidence':False,'member_results':results,'runtime_error_count':errors,'status':'COMPLETED_WITH_RUNTIME_ERRORS' if errors else 'COMPLETED','note':'Child return codes are execution status only; scientific gate state remains in each fresh member ledger.'})
    return 1 if errors else 0

if __name__=='__main__': raise SystemExit(main())
