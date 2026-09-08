from pathlib import Path
import argparse,csv,hashlib,json,math,platform,sys,time,numpy as np
from . import __version__
from .io import discover_curves
from .blind import blind_id
from .gates import gate_reparameterization,gate_phase,gate_redundancy,gate_dynamics,temporal_convergence,spatial_convergence
from .constants import *
from .report import write_report


def _j(v):
    if isinstance(v,(np.floating,np.integer)): return v.item()
    if isinstance(v,np.ndarray): return v.tolist()
    if isinstance(v,float) and not math.isfinite(v): return None
    if isinstance(v,dict): return {k:_j(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)): return [_j(x) for x in v]
    return v


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for c in iter(lambda:f.read(1<<20),b''): h.update(c)
    return h.hexdigest()


def write_csv(path,rows):
    if not rows: Path(path).write_text('',encoding='utf-8'); return
    fields=[]
    for r in rows:
        for k in r:
            if k not in fields: fields.append(k)
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k:_j(v) for k,v in r.items()})


def run(config_path,dataset_dir,outdir):
    cp=Path(config_path).resolve(); dd=Path(dataset_dir).resolve(); od=Path(outdir).resolve()
    od.mkdir(parents=True,exist_ok=True)
    cfg=json.loads(cp.read_text()); salt=str(cfg.get('blind_salt','SST-MP-EFT-v0.1.1'))
    raw=discover_curves(dd)
    records=[]
    for p,x in raw:
        rel=str(p.relative_to(dd)); bid=blind_id(rel,salt)
        records.append((bid,p,x,rel))
    records.sort(key=lambda r:r[0])  # blind deterministic selection, not topology/name order
    mx=int(cfg.get('max_samples',0))
    if mx>0: records=records[:mx]
    if not records: raise SystemExit(f'No readable coordinate curves under {dd}')

    certlim=int(cfg.get('certification_max_samples',0))
    cert_ids=set(r[0] for r in records[:certlim]) if certlim>0 else set(r[0] for r in records)
    manifest={
        'version':__version__,
        'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'python':sys.version,'platform':platform.platform(),
        'config_sha256':sha(cp),'dataset_dir':str(dd),
        'selection':'blind_id lexical order; max_samples=0 means all',
        'certification_blind_ids':sorted(cert_ids),
        'constants':{
            'v_swirl_m_s':V_SWIRL,'r_c_m':R_C,'rho_core_kg_m3':RHO_CORE,
            'rho_f_kg_m3':RHO_F,'gamma_m2_s':GAMMA,'t_core_s':T_CORE,
            'omega_core_s-1':OMEGA_CORE,'f_core_Hz':F_CORE,'gamma_star':GAMMA_STAR
        },'config':cfg
    }
    (od/'manifest.json').write_text(json.dumps(_j(manifest),indent=2))

    key=[]; gates=[]; modes=[]; samples=[]
    names=['G1_REPARAM','G2_PHASE','G3_REDUNDANCY','G4_DISPERSION','T_CONV','S_CONV']
    counts={g:{'PASS':0,'FAIL':0,'SKIP':0} for g in names}

    for bid,p,x,rel in records:
        key.append({'blind_id':bid,'relative_path':rel,'sha256':sha(p)})
        g1=gate_reparameterization(x,cfg['gates']['reparameterization'])
        g2=gate_phase(x,cfg['gates']['phase'])
        g3=gate_redundancy(x,cfg['gates']['redundancy'])
        g4=gate_dynamics(x,cfg['gates']['dynamics'])
        cert=bid in cert_ids
        tc=temporal_convergence(x,cfg['gates']['temporal_convergence']) if cert else {'status':'SKIP'}
        sc=spatial_convergence(x,cfg['gates']['spatial_convergence']) if cert else {'status':'SKIP'}
        for name,g in [(names[0],g1),(names[1],g2),(names[2],g3),(names[3],g4),(names[4],tc),(names[5],sc)]:
            st=g.get('status','SKIP'); st=st if st in counts[name] else 'SKIP'
            counts[name][st]+=1
            gates.append({'blind_id':bid,'gate':name,'status':st,
                          'metric':g.get('metric',g.get('relative_error')),
                          'threshold':g.get('threshold'),
                          'details_json':json.dumps(_j(g),separators=(',',':'))})
        for r in g4.get('mode_rows',[]):
            rr=dict(r); rr['blind_id']=bid; modes.append(rr)
        samples.append({
            'blind_id':bid,'n_input':len(x),
            'G1':g1['status'],'G1_metric':g1.get('metric'),
            'G2':g2['status'],'G2_holonomy_rad':g2.get('holonomy_n3_rad') if g2.get('holonomy_n3_rad') is not None else g2.get('holonomy_n2_rad'),
            'G2_physical_phase_lock':g2.get('physical_phase_lock_status'),
            'G3':g3['status'],'G3_metric':g3.get('metric'),
            'G4':g4['status'],'G4_rel_rmse':g4.get('dispersion',{}).get('rel_rmse'),
            'G4_a2':g4.get('dispersion',{}).get('a2'),'G4_a4':g4.get('dispersion',{}).get('a4'),
            'G4_quartic_gain':g4.get('dispersion',{}).get('quartic_relative_improvement'),
            'T_CONV':tc.get('status'),'S_CONV':sc.get('status')
        })

    write_csv(od/'blind_key.csv',key); write_csv(od/'gate_results.csv',gates)
    write_csv(od/'mode_results.csv',modes); write_csv(od/'sample_summary.csv',samples)

    t_enabled=bool(cfg['gates']['temporal_convergence'].get('enabled',False))
    s_enabled=bool(cfg['gates']['spatial_convergence'].get('enabled',False))
    cert_fail=(t_enabled and counts['T_CONV']['FAIL']>0) or (s_enabled and counts['S_CONV']['FAIL']>0)
    physical_fail=counts['G4_DISPERSION']['FAIL']>0
    physical_inconclusive=counts['G4_DISPERSION']['SKIP']>0
    diagnostic_fail=any(counts[g]['FAIL']>0 for g in ['G1_REPARAM','G2_PHASE','G3_REDUNDANCY'])

    if cert_fail:
        overall='NUMERICALLY_INCONCLUSIVE'
    elif physical_fail:
        overall='CLOSURE_FAIL'
    elif physical_inconclusive:
        overall='INCONCLUSIVE'
    elif t_enabled or s_enabled:
        overall='CLOSURE_SURVIVED_WITH_WARNINGS' if diagnostic_fail else 'CLOSURE_SURVIVED'
    else:
        overall='PRELIMINARY_SURVIVED_WITH_WARNINGS' if diagnostic_fail else 'PRELIMINARY_SURVIVED'

    summary={
        'version':__version__,'n_samples':len(records),'gate_counts':counts,
        'overall_status':overall,
        'diagnostic_warning_present':diagnostic_fail,
        'verdict_semantics':{
            'G1':'centerline relabeling numerical surrogate',
            'G2':'geometric candidate-phase diagnostic unless physical phase lock is explicitly enabled',
            'G3':'operator-identity/implementation pre-gate',
            'G4':'tested finite-core local-response closure',
            'T_CONV_S_CONV':'numerical certification gates'
        }
    }
    (od/'summary.json').write_text(json.dumps(_j(summary),indent=2))
    write_report(od,summary)
    print(json.dumps(summary,indent=2)); print('[SST-EFT] outputs:',od)


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--dataset',required=True); ap.add_argument('--outdir',required=True)
    a=ap.parse_args(); run(a.config,a.dataset,a.outdir)


if __name__=='__main__': main()
