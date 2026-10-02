from __future__ import annotations
import argparse, json, traceback, re
from pathlib import Path
import numpy as np
from .common import load_json,dump_json,write_csv,nowstamp,sha256_file,geometry_sha256,relerr
from .geometry import load_geometry,normalize_components,discover
from .relative_equilibrium import fit_relative_equilibrium
from .perturb import perturbed
from .dynamics import evolve
from .modal import aligned_displacement,pod_freeze,dominant_frequency
from .energy import physical_line_energy
from .native_ext import NATIVE_AVAILABLE

def mode_run(X,offs,eps,cfg,sc,phi_mu=None,cfl_divisor=1.0):
    Xp=perturbed(X,offs,eps,+1); Xm=perturbed(X,offs,eps,-1)
    tp,sp,dp=evolve(Xp,offs,cfg,cfg.get('samples',192),cfl_divisor=cfl_divisor)
    tm,sm,dm=evolve(Xm,offs,cfg,cfg.get('samples',192),cfl_divisor=cfl_divisor)
    n=min(len(tp),len(tm));times=tp[:n]
    odd=(aligned_displacement(sp[:n],X)-aligned_displacement(sm[:n],X))/(2*eps)
    if phi_mu is None:
        phi,mu,coef,k,frac=pod_freeze(odd,cfg.get('discovery_fraction',0.4)); frozen=(phi,mu)
    else:
        phi,mu=phi_mu;k=max(8,int(len(odd)*cfg.get('discovery_fraction',0.4)));coef=(odd-mu)@phi;frac=float('nan');frozen=phi_mu
    fq=dominant_frequency(times,coef,k)
    return fq,dp,dm,frozen,frac

def run_case(path,cfg,resolution,eps_list):
    comps=load_geometry(path); X,offs=normalize_components(comps,resolution)
    reinfo=fit_relative_equilibrium(X,offs,1.0,cfg['core_fraction'],cfg.get('require_native',False))
    E0,_,sc=physical_line_energy(X,offs,cfg['core_fraction'],cfg.get('require_native',False))
    rows=[];frozen=None
    for eps in eps_list:
        Xp=perturbed(X,offs,eps,+1);Xm=perturbed(X,offs,eps,-1)
        Ep,_,_=physical_line_energy(Xp,offs,cfg['core_fraction'],cfg.get('require_native',False));Em,_,_=physical_line_energy(Xm,offs,cfg['core_fraction'],cfg.get('require_native',False));dE=0.5*(Ep+Em)-E0
        fq,dp,dm,frozen,frac=mode_run(X,offs,eps,cfg,sc,frozen,1.0)
        fphys=fq['frequency']/sc['time_scale_s'];ophys=fq['omega']/sc['time_scale_s']
        rows.append({'amplitude':eps,'delta_E_J':dE,'base_energy_J':E0,'delta_E_over_abs_base':dE/max(abs(E0),1e-300),'energy_signal_valid':bool(np.isfinite(dE) and dE>0),'frequency_Hz':fphys,'omega_rad_s':ophys,'frequency_dimless':fq['frequency'],'spectral_power':fq['spectral_power'],'cycles':fq['cycles'],'period_cv':fq['period_cv'],'harmonic_r2':fq['harmonic_r2'],'pod_discovery_fraction':frac,'epsilon_RE':reinfo['epsilon_RE'],'mesh_cv_plus':dp['sample_mesh_max_cv'],'mesh_cv_minus':dm['sample_mesh_max_cv'],'dt_min':dp['dt_min'],'dt_max':dp['dt_max'],'n_steps':dp['n_steps'],'L_phys_m':sc['L_phys_m'],'Gamma_phys_m2_s':sc['Gamma_phys_m2_s'],'rho_energy_kg_m3':sc['rho_f_kg_m3']})
    # Temporal convergence is certified on the smallest probe at fixed T_final.
    freqs=[]
    for fac in cfg.get('temporal_refinement_factors',[1,2]):
        fq,_,_,_,_=mode_run(X,offs,eps_list[0],cfg,sc,None,float(fac));freqs.append((float(fac),fq['frequency']))
    temporal_rel=None
    if len(freqs)>=2 and freqs[-2][1]>0: temporal_rel=relerr(freqs[-1][1],freqs[-2][1])
    for r in rows:r['temporal_frequency_rel_change']=temporal_rel if temporal_rel is not None else ''
    return X,offs,reinfo,rows,{'frequency_by_cfl_divisor':freqs,'highest_refinement_rel_change':temporal_rel}

def main():
    p=argparse.ArgumentParser();p.add_argument('dataset');p.add_argument('--config',default='config/basic.json');p.add_argument('--out',default=None);a=p.parse_args();cfg=load_json(a.config);out=Path(a.out or f'outputs/basic_{nowstamp()}');out.mkdir(parents=True,exist_ok=True)
    files=discover(a.dataset); regex=cfg.get('source_regex')
    if regex: files=[f for f in files if re.search(regex,f.name,re.I)]
    files=files[:int(cfg.get('max_carriers',6))]
    if not files: raise SystemExit('No candidate geometry files found')
    allrows=[];public_cases=[];private_cases=[]
    for ci,f in enumerate(files):
        try:
            for N in cfg['resolution_ladder']:
                X,o,reinfo,rows,tconv=run_case(f,cfg,int(N),cfg['amplitudes']); src_hash=sha256_file(f);geo_hash=geometry_sha256(X,o)
                for r in rows:r.update({'case_index':ci,'source_name':f.name,'source_path':str(f),'source_sha256':src_hash,'geometry_sha256':geo_hash,'resolution_N':N,'family_hint':f.stem})
                allrows+=rows
                public_cases.append({'case_index':ci,'resolution_N':N,'relative_equilibrium':reinfo,'temporal_convergence':tconv,'status':'OK'})
                private_cases.append({'case_index':ci,'source_name':f.name,'source_path':str(f),'source_sha256':src_hash,'geometry_sha256':geo_hash,'resolution_N':N})
        except Exception as e:
            public_cases.append({'case_index':ci,'status':'ERROR','error':repr(e)});private_cases.append({'case_index':ci,'source_name':f.name,'source_path':str(f),'status':'ERROR','traceback':traceback.format_exc()[-3000:]})
    write_csv(out/'raw_observations.csv',allrows)
    dump_json(out/'campaign.json',{'format':'SST-WP-CAMPAIGN-PUBLIC-2.0','config':cfg,'native_available':NATIVE_AVAILABLE,'dataset_root_hash_hint':'identity withheld until reveal','cases':public_cases,'observations':len(allrows),'action_energy_density':'rho_f only','rho_core_used_for_action':False,'topology_certified_by_this_package':False})
    dump_json(out/'campaign_private.json',{'format':'SST-WP-CAMPAIGN-PRIVATE-2.0','dataset':str(Path(a.dataset).resolve()),'cases':private_cases})
    print(json.dumps({'out':str(out),'files':len(files),'observations':len(allrows),'errors':sum(c['status']!='OK' for c in public_cases),'native_available':NATIVE_AVAILABLE},indent=2))
if __name__=='__main__':main()
