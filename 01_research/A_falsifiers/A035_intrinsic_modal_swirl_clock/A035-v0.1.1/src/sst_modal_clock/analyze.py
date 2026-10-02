from pathlib import Path
import csv,json
import numpy as np
from .blind import load_catalog
from .modal import odd_response,learn_modes,project,mode_strain_weights,recurrence_metrics,delayed_stretch_test
from .util import clean_json

def _load(p): return np.load(p,allow_pickle=False)
def _mode_score(r):
    return float(r.get('spectral_power_fraction',0))*max(0,float(r.get('harmonic_r2',0)))*(1/(1+max(0,float(r.get('recurrence_closure_error',99) or 99))))

def analyze(work,cfg):
    work=Path(work); cat=load_catalog(work); pairs={}
    for r in cat:pairs.setdefault(r['pair_id'],[]).append(r)
    allm=[]; carriers=[]
    for pid,rr in sorted(pairs.items()):
        rp=next((r for r in rr if int(r['probe_arm'])==1),None); rm=next((r for r in rr if int(r['probe_arm'])==-1),None)
        if not rp or not rm:continue
        paths={}
        ok=True
        for branch in ('material','fixed'):
            pp=work/f'results_{branch}/candidates/{rp["candidate_id"]}.npz'; pm=work/f'results_{branch}/candidates/{rm["candidate_id"]}.npz'
            if not pp.exists() or not pm.exists():ok=False;break
            paths[branch]=(_load(pp),_load(pm))
        if not ok:continue
        mp,mm=paths['material']; fp,fm=paths['fixed']; t=np.asarray(mp['t'],float)
        if not (len(t)==len(mm['t'])==len(fp['t'])==len(fm['t'])):continue
        mat,ref=odd_response(mp,mm,cfg['probe_eps']); fix,_=odd_response(fp,fm,cfg['probe_eps']); nd=max(8,min(len(t)-8,int(round(float(cfg.get('discovery_fraction',.4))*len(t))))); modes,ev=learn_modes(mat,nd,int(cfg.get('top_modes',6))); amat=project(mat,modes); afix=project(fix,modes); sigm=.5*(np.asarray(mp['sigma'])-np.asarray(mm['sigma']))/max(float(cfg['probe_eps']),1e-15); sigf=.5*(np.asarray(fp['sigma'])-np.asarray(fm['sigma']))/max(float(cfg['probe_eps']),1e-15); candidate_modes=[]
        for k,mode in enumerate(modes):
            rmdisc=recurrence_metrics(t[:nd],amat[:nd,k]); rmtr=recurrence_metrics(t[nd:],amat[nd:,k]); rftr=recurrence_metrics(t[nd:],afix[nd:,k]); w=mode_strain_weights(mode,ref); sm=sigm@w; sf=sigf@w
            # Delay selection is discovery-only: never use a holdout-derived period to choose the lag search window.
            disc_period=rmdisc.get('period',np.nan) if rmdisc.get('valid') else np.nan
            delay=delayed_stretch_test(t,amat[:,k],sm,disc_period,float(cfg.get('discovery_fraction',.4)),int(cfg.get('n_phase_nulls',31))) if rmtr.get('valid') else {}
            sc1=bool(ev[k]>=float(cfg.get('gate_min_discovery_energy',.03)) and rmtr.get('amplitude',0)>=float(cfg.get('gate_min_holdout_amplitude',1e-5)))
            ratio=float(rmtr.get('late_to_early_rms_ratio',99) or 99); closure=rmtr.get('recurrence_closure_error'); closure=99 if closure is None else float(closure)
            geometry_ok=bool(max(np.max(mp['ds_cv']),np.max(mm['ds_cv']))<=float(cfg.get('gate_max_ds_cv',.45)))
            sc2=bool(geometry_ok and rmtr.get('valid') and rmtr.get('cycles',0)>=float(cfg.get('gate_min_cycles',1.5)) and rmtr.get('spectral_power_fraction',0)>=float(cfg.get('gate_min_spectral_power',.30)) and rmtr.get('harmonic_r2',0)>=float(cfg.get('gate_min_harmonic_r2',.45)) and closure<=float(cfg.get('gate_max_closure_error',.45)) and float(cfg.get('gate_min_amp_ratio',.4))<=ratio<=float(cfg.get('gate_max_amp_ratio',2.5)))
            sc3=bool(delay and abs(delay.get('holdout_corr',0))>=float(cfg.get('gate_min_stretch_accel_corr',.30)) and delay.get('phase_null_p',1)<=float(cfg.get('gate_max_phase_null_p',.10)))
            sc4=bool(sc3 and delay.get('delay',0)>=2*np.median(np.diff(t)) and delay.get('delay_advantage_abs_corr',-99)>=float(cfg.get('gate_min_delay_advantage',.05)))
            smat=_mode_score(rmtr); sfix=_mode_score(rftr); fixed_pass=bool(rftr.get('valid') and rftr.get('cycles',0)>=float(cfg.get('gate_min_cycles',1.5)) and rftr.get('spectral_power_fraction',0)>=float(cfg.get('gate_min_spectral_power',.30)) and rftr.get('harmonic_r2',0)>=float(cfg.get('gate_min_harmonic_r2',.45)))
            sc5=bool(sc1 and sc2 and sc3 and sc4 and ((not fixed_pass) or smat-sfix>=float(cfg.get('gate_min_material_over_fixed_score',.05))))
            row={'pair_id':pid,'carrier_id':rp['carrier_id'],'mode_index':k,'discovery_energy_fraction':float(ev[k]),'discovery_period':rmdisc.get('period'),'geometry_ok':geometry_ok,**{f'material_{a}':b for a,b in rmtr.items()},**{f'fixed_{a}':b for a,b in rftr.items()},**{f'stretch_{a}':b for a,b in delay.items()},'material_clock_score':smat,'fixed_clock_score':sfix,'SC1_intrinsic_mode':sc1,'SC2_recurrence':sc2,'SC3_stretch_coupling':sc3,'SC4_measured_delay':sc4,'SC5_core_specificity':sc5,'clock_candidate':bool(sc5)}
            allm.append(row); candidate_modes.append(row)
        best=max(candidate_modes,key=lambda r:(int(r['clock_candidate']),r['material_clock_score']),default=None); carriers.append({'carrier_id':rp['carrier_id'],'n_modes':len(candidate_modes),'n_clock_candidates':sum(int(r['clock_candidate']) for r in candidate_modes),'best_mode_index':best['mode_index'] if best else None,'best_material_clock_score':best['material_clock_score'] if best else None,'best_SC2_recurrence':best['SC2_recurrence'] if best else False,'best_SC5_core_specificity':best['SC5_core_specificity'] if best else False,'max_ds_cv_material':float(max(np.max(mp['ds_cv']),np.max(mm['ds_cv']))),'max_ds_cv_fixed':float(max(np.max(fp['ds_cv']),np.max(fm['ds_cv'])))})
    out=work/'analysis'; out.mkdir(parents=True,exist_ok=True)
    def savecsv(name,rows):
        fields=sorted(set().union(*(r.keys() for r in rows))) if rows else ['carrier_id'];
        with open(out/name,'w',newline='',encoding='utf-8') as f:
            z=csv.DictWriter(f,fieldnames=fields);z.writeheader();z.writerows(rows)
    savecsv('blind_modal_results.csv',allm);savecsv('blind_carrier_summary.csv',carriers)
    cand=[r for r in allm if r['clock_candidate']]; rec=[r for r in allm if r['SC2_recurrence']]; summary={'format':'SST-INTRINSIC-MODAL-CLOCK-BLIND-1.0','n_carriers':len(carriers),'n_modes_tested':len(allm),'n_recurrent_modes':len(rec),'n_clock_candidates':len(cand),'carriers_with_clock_candidates':len(set(r['carrier_id'] for r in cand)),'carrier_identity_read':False,'qhp_coordinate_used':False,'mode_basis_source':'material-core discovery window POD/SVD; frozen for holdout and fixed-core null','discovery_fraction':float(cfg.get('discovery_fraction',.4)),'primary_gate':'PASS_CANDIDATE_INTRINSIC_SWIRL_CLOCK' if cand else ('FAIL_RECURRENCE_WITHOUT_CAUSAL_CLOCK' if rec else 'FAIL_NO_INTRINSIC_RECURRENT_MODE')}
    (out/'blind_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return summary
