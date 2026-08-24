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
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader();
        for r in rows: w.writerow({k:_j(v) for k,v in r.items()})
def run(config_path,dataset_dir,outdir):
    cp=Path(config_path).resolve(); dd=Path(dataset_dir).resolve(); od=Path(outdir).resolve(); od.mkdir(parents=True,exist_ok=True); cfg=json.loads(cp.read_text()); curves=discover_curves(dd); mx=int(cfg.get('max_samples',0)); curves=curves[:mx] if mx>0 else curves
    if not curves: raise SystemExit(f'No readable coordinate curves under {dd}')
    manifest={'version':__version__,'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'python':sys.version,'platform':platform.platform(),'config_sha256':sha(cp),'dataset_dir':str(dd),'constants':{'v_swirl_m_s':V_SWIRL,'r_c_m':R_C,'rho_core_kg_m3':RHO_CORE,'rho_f_kg_m3':RHO_F,'gamma_m2_s':GAMMA,'t_core_s':T_CORE,'omega_core_s-1':OMEGA_CORE,'f_core_Hz':F_CORE,'gamma_star':GAMMA_STAR},'config':cfg}; (od/'manifest.json').write_text(json.dumps(_j(manifest),indent=2))
    key=[]; gates=[]; modes=[]; samples=[]; names=['G1_REPARAM','G2_PHASE','G3_REDUNDANCY','G4_DISPERSION','T_CONV','S_CONV']; counts={g:{'PASS':0,'FAIL':0,'SKIP':0} for g in names}; certlim=int(cfg.get('certification_max_samples',0)); salt=str(cfg.get('blind_salt','SST-MP-EFT-v0.1.0'))
    for idx,(p,x) in enumerate(curves):
        rel=str(p.relative_to(dd)); bid=blind_id(rel,salt); key.append({'blind_id':bid,'relative_path':rel,'sha256':sha(p)}); g1=gate_reparameterization(x,cfg['gates']['reparameterization']); g2=gate_phase(x,cfg['gates']['phase']); g3=gate_redundancy(x,cfg['gates']['redundancy']); g4=gate_dynamics(x,cfg['gates']['dynamics']); cert=certlim<=0 or idx<certlim; tc=temporal_convergence(x,cfg['gates']['temporal_convergence']) if cert else {'status':'SKIP'}; sc=spatial_convergence(x,cfg['gates']['spatial_convergence']) if cert else {'status':'SKIP'}
        for name,g in [(names[0],g1),(names[1],g2),(names[2],g3),(names[3],g4),(names[4],tc),(names[5],sc)]:
            st=g.get('status','SKIP'); st=st if st in counts[name] else 'SKIP'; counts[name][st]+=1; gates.append({'blind_id':bid,'gate':name,'status':st,'metric':g.get('metric',g.get('relative_error')),'threshold':g.get('threshold'),'details_json':json.dumps(_j(g),separators=(',',':'))})
        for r in g4.get('mode_rows',[]): rr=dict(r); rr['blind_id']=bid; modes.append(rr)
        samples.append({'blind_id':bid,'n_input':len(x),'G1':g1['status'],'G1_metric':g1.get('metric'),'G2':g2['status'],'G2_holonomy_rad':g2.get('holonomy_n2_rad'),'G2_physical_phase_lock':g2.get('physical_phase_lock_status'),'G3':g3['status'],'G3_metric':g3.get('metric'),'G4':g4['status'],'G4_rel_rmse':g4.get('dispersion',{}).get('rel_rmse'),'G4_a2':g4.get('dispersion',{}).get('a2'),'G4_a4':g4.get('dispersion',{}).get('a4'),'T_CONV':tc.get('status'),'S_CONV':sc.get('status')})
    write_csv(od/'blind_key.csv',key); write_csv(od/'gate_results.csv',gates); write_csv(od/'mode_results.csv',modes); write_csv(od/'sample_summary.csv',samples); cert_fail=(cfg['gates']['temporal_convergence'].get('enabled',False) and counts['T_CONV']['FAIL']>0) or (cfg['gates']['spatial_convergence'].get('enabled',False) and counts['S_CONV']['FAIL']>0); core_fail=any(counts[g]['FAIL']>0 for g in ['G1_REPARAM','G2_PHASE','G3_REDUNDANCY','G4_DISPERSION']); dyn_inconclusive=cfg['gates']['dynamics'].get('enabled',True) and counts['G4_DISPERSION']['PASS']==0 and counts['G4_DISPERSION']['FAIL']==0; overall='FAIL' if (core_fail or cert_fail) else ('INCONCLUSIVE' if dyn_inconclusive else 'PASS'); summary={'version':__version__,'n_samples':len(curves),'gate_counts':counts,'overall_status':overall}; (od/'summary.json').write_text(json.dumps(_j(summary),indent=2)); write_report(od,summary); print(json.dumps(summary,indent=2)); print('[SST-EFT] outputs:',od)
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--dataset',required=True); ap.add_argument('--outdir',required=True); a=ap.parse_args(); run(a.config,a.dataset,a.outdir)
if __name__=='__main__': main()
