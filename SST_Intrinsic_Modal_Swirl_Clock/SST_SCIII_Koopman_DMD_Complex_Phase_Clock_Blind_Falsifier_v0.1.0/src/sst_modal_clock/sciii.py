from __future__ import annotations
from pathlib import Path
import csv,json,math
import numpy as np

from .blind import load_catalog
from .modal import natural_response, odd_response, even_probe_contamination, learn_modes, project, mode_strain_weights
from .analyze import _stage_a_geometry_metrics
from .sc2 import _pairs,_arm,_stage_a_file,_stage_b_file,_cut,_coverage_gate,_rel_spread,_corr
from .sciib import _phase_core_metrics, delayed_pair_phase_modulation_test
from .util import clean_json


def _savecsv(path,rows):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); fields=sorted(set().union(*(r.keys() for r in rows))) if rows else ['carrier_id']
    with open(path,'w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows: w.writerow({k:(json.dumps(clean_json(v),sort_keys=True) if isinstance(v,(list,dict,tuple)) else v) for k,v in r.items()})


def _manifest(work,name):
    p=Path(work)/'analysis'/name
    return json.loads(p.read_text(encoding='utf-8')).get('candidates',[]) if p.exists() else []


def _dmd_matrix(X):
    X=np.asarray(X,float)
    if len(X)<8: raise ValueError('too few DMD samples')
    X1=X[:-1].T; X2=X[1:].T
    return X2@np.linalg.pinv(X1,rcond=1e-10)


def _eig_candidates(A,dt):
    vals,vr=np.linalg.eig(A); vals_l,vl=np.linalg.eig(A.T); out=[]
    for i,lam in enumerate(vals):
        ang=float(np.angle(lam))
        if ang<=1e-8 or abs(lam)<1e-12: continue
        j=int(np.argmin(np.abs(vals_l-lam)))
        right=np.asarray(vr[:,i],complex); left=np.asarray(vl[:,j],complex)
        left=left/max(np.linalg.norm(left),1e-15); right=right/max(np.linalg.norm(right),1e-15)
        omega=ang/max(dt,1e-15); sigma=float(np.log(max(abs(lam),1e-15))/max(dt,1e-15))
        out.append({'lambda':complex(lam),'left':left,'right':right,'omega':float(omega),'frequency':float(omega/(2*np.pi)),'sigma':sigma,'growth_to_omega':float(abs(sigma)/max(abs(omega),1e-15))})
    return out


def _discovery_candidates(t,X,cfg):
    t=np.asarray(t,float); X=np.asarray(X,float); dt=float(np.median(np.diff(t))); A=_dmd_matrix(X); total=max(float(np.mean(np.sum(X*X,axis=1))),1e-30); out=[]
    for c in _eig_candidates(A,dt):
        q=X@c['left']; ef=float(np.mean(np.abs(q)**2)/total); resid=float(np.linalg.norm(q[1:]-c['lambda']*q[:-1])/max(np.linalg.norm(q[1:]),1e-15)); cycles=float((t[-1]-t[0])*c['frequency'])
        out.append({**c,'coordinate_energy_fraction':ef,'eigen_relation_residual':resid,'discovery_cycles':cycles})
    return sorted(out,key=lambda z:(z['coordinate_energy_fraction'],-z['eigen_relation_residual']),reverse=True)


def _q1(c,cfg):
    return bool(c and c['coordinate_energy_fraction']>=float(cfg.get('sciii_gate_min_coordinate_energy',0.03)) and c['growth_to_omega']<=float(cfg.get('sciii_gate_max_discovery_growth_to_omega',0.20)) and c['eigen_relation_residual']<=float(cfg.get('sciii_gate_max_discovery_eigen_residual',0.40)) and c['discovery_cycles']>=float(cfg.get('sciii_gate_min_discovery_cycles',0.60)))


def _complex_overlap(a,b):
    a=np.asarray(a,complex); b=np.asarray(b,complex); return float(abs(np.vdot(a,b))/max(np.linalg.norm(a)*np.linalg.norm(b),1e-15))


def _align_gauge(prev,w):
    z=np.vdot(prev,w)
    return w*np.exp(-1j*np.angle(z)) if abs(z)>1e-15 else w


def _local_continuation(t,X,reference,cfg,gauge_phases=None):
    t=np.asarray(t,float); X=np.asarray(X,float); dt=float(np.median(np.diff(t))); f0=float(reference['frequency']); T0=1/max(f0,1e-15)
    win=max(int(cfg.get('sciii_min_window_samples',40)),int(round(float(cfg.get('sciii_window_cycles',2.0))*T0/dt))); win=min(win,max(40,len(t)//2)); step=max(4,int(round(float(cfg.get('sciii_window_step_fraction',0.35))*win)))
    starts=list(range(0,max(1,len(t)-win+1),step))
    if starts and starts[-1]+win<len(t): starts.append(len(t)-win)
    prev=np.asarray(reference['left'],complex); prevf=f0; loc=[]
    for wi,st in enumerate(starts):
        en=min(len(t),st+win)
        if en-st<max(24,int(cfg.get('sciii_min_window_samples',40))): continue
        try: cs=_eig_candidates(_dmd_matrix(X[st:en]),dt)
        except Exception: continue
        best=None
        for c in cs:
            ov=_complex_overlap(prev,c['left']); fd=abs(c['frequency']-prevf)/max(abs(prevf),1e-15); score=ov-0.35*fd
            if best is None or score>best[0]: best=(score,ov,fd,c)
        if best is None: continue
        _,ov,fd,c=best
        w=np.asarray(c['left'],complex)
        if gauge_phases is not None and wi<len(gauge_phases): w=w*np.exp(1j*float(gauge_phases[wi]))
        w=_align_gauge(prev,w); center=(st+en-1)//2
        q=X[st:en]@w; ph=np.unwrap(np.angle(q)); k0=max(0,len(q)//3); q0=q[k0]; pred=np.angle(q0)+np.arange(len(q)-k0)*np.angle(c['lambda']); act=np.unwrap(np.angle(q[k0:])); pred=pred+(act[0]-pred[0]); err=act-pred
        loc.append({'start':st,'end':en,'center':center,'left':w,'right':np.asarray(c['right'],complex),'lambda':c['lambda'],'frequency':c['frequency'],'omega':c['omega'],'sigma':c['sigma'],'growth_to_omega':c['growth_to_omega'],'overlap':ov,'frequency_jump_rel':fd,'prediction_rms':float(np.sqrt(np.mean(err*err))) if len(err) else np.inf,'prediction_terminal':float(abs(err[-1])) if len(err) else np.inf})
        prev=w; prevf=float(c['frequency'])
    return loc, len(starts)


def _interpolated_coordinate(t,X,loc,reference):
    t=np.asarray(t,float); X=np.asarray(X,float); n=len(t); d=X.shape[1]
    if not loc:
        w=np.tile(np.asarray(reference['left'],complex),(n,1))
    else:
        centers=np.asarray([z['center'] for z in loc],float); W=np.vstack([z['left'] for z in loc]); idx=np.arange(n,float) if False else np.arange(n,dtype=float); w=np.empty((n,d),complex)
        for j in range(d): w[:,j]=np.interp(idx,centers,W[:,j].real,left=W[0,j].real,right=W[-1,j].real)+1j*np.interp(idx,centers,W[:,j].imag,left=W[0,j].imag,right=W[-1,j].imag)
        w=w/np.maximum(np.linalg.norm(w,axis=1)[:,None],1e-15)
    q=np.sum(X*w,axis=1)
    ph=np.unwrap(np.angle(q))
    if len(ph)>2 and np.polyfit(t,ph,1)[0]<0: q=np.conj(q)
    return q


def sciii_metrics(t,X,reference,cfg,gauge_phases=None):
    t=np.asarray(t,float); X=np.asarray(X,float); loc,n_attempted=_local_continuation(t,X,reference,cfg,gauge_phases=gauge_phases); q=_interpolated_coordinate(t,X,loc,reference); core=_phase_core_metrics(t,q.real,q.imag,cfg)
    matched_fraction=float(len(loc)/max(n_attempted,1)); ovs=np.asarray([z['overlap'] for z in loc],float); freqs=np.asarray([z['frequency'] for z in loc],float); gr=np.asarray([z['growth_to_omega'] for z in loc],float); pr=np.asarray([z['prediction_rms'] for z in loc],float); pt=np.asarray([z['prediction_terminal'] for z in loc],float)
    cont={'n_local_windows':len(loc),'continuation_matched_fraction':min(1.0,matched_fraction),'mode_overlap_median':float(np.median(ovs)) if len(ovs) else 0.0,'mode_overlap_min':float(np.min(ovs)) if len(ovs) else 0.0,'local_frequency_cv':float(np.std(freqs)/max(abs(np.mean(freqs)),1e-15)) if len(freqs)>=2 else np.inf,'local_frequency_median':float(np.median(freqs)) if len(freqs) else np.nan,'local_growth_to_omega_median':float(np.median(gr)) if len(gr) else np.inf,'local_growth_to_omega_max':float(np.max(gr)) if len(gr) else np.inf,'local_prediction_rms_median_rad':float(np.median(pr)) if len(pr) else np.inf,'local_prediction_terminal_median_rad':float(np.median(pt)) if len(pt) else np.inf}
    return {**core,**cont,'coordinate_radius_median':core.get('radius_median'),'local_windows':[{k:(v.tolist() if isinstance(v,np.ndarray) else ([v.real,v.imag] if isinstance(v,complex) else v)) for k,v in z.items() if k not in {'left','right'}} for z in loc]},q,loc


def sciii_gates(discovery,m,cfg,channel):
    q1=_q1(discovery,cfg)
    q2=bool(m.get('continuation_matched_fraction',0)>=float(cfg.get('sciii_gate_min_continuation_fraction',0.75)) and m.get('mode_overlap_median',0)>=float(cfg.get('sciii_gate_min_mode_overlap_median',0.65)) and m.get('mode_overlap_min',0)>=float(cfg.get('sciii_gate_min_mode_overlap_min',0.35)) and m.get('local_frequency_cv',99)<=float(cfg.get('sciii_gate_max_local_frequency_cv',0.25)))
    q3=bool(m.get('phase_wraps',0)>=float(cfg.get('sciii_gate_min_phase_wraps',4.0)) and m.get('phase_monotonic_fraction',0)>=float(cfg.get('sciii_gate_min_monotonic_fraction',0.90)) and m.get('phase_linearity_r2',0)>=float(cfg.get('sciii_gate_min_phase_linearity_r2',0.90)) and m.get('period_cv',99)<=float(cfg.get('sciii_gate_max_period_cv',0.15)) and m.get('phase_diffusion_rms_rad',99)<=float(cfg.get('sciii_gate_max_phase_diffusion_rms_rad',0.75)))
    q4=bool(m.get('radius_cv',99)<=float(cfg.get('sciii_gate_max_radius_cv',0.60)) and float(cfg.get('sciii_gate_min_radius_retention_ratio',0.40))<=m.get('radius_retention_ratio',0)<=float(cfg.get('sciii_gate_max_radius_retention_ratio',2.50)) and m.get('radius_reliable_fraction',0)>=float(cfg.get('sciii_gate_min_radius_reliable_fraction',0.80)) and m.get('local_growth_to_omega_median',99)<=float(cfg.get('sciii_gate_max_local_growth_to_omega',0.25)))
    q5=bool(m.get('local_prediction_rms_median_rad',99)<=float(cfg.get('sciii_gate_max_local_prediction_rms_rad',1.00)) and m.get('local_prediction_terminal_median_rad',99)<=float(cfg.get('sciii_gate_max_local_prediction_terminal_rad',1.57)))
    q6=(channel=='natural')
    return q1,q2,q3,q4,q5,q6


def _serialize_discovery(c):
    return {'lambda':[float(c['lambda'].real),float(c['lambda'].imag)],'left_real':c['left'].real.tolist(),'left_imag':c['left'].imag.tolist(),'right_real':c['right'].real.tolist(),'right_imag':c['right'].imag.tolist(),'omega':c['omega'],'frequency':c['frequency'],'sigma':c['sigma'],'growth_to_omega':c['growth_to_omega'],'coordinate_energy_fraction':c['coordinate_energy_fraction'],'eigen_relation_residual':c['eigen_relation_residual'],'discovery_cycles':c['discovery_cycles']}


def _deserialize_discovery(c):
    return {'lambda':complex(*c['lambda']),'left':np.asarray(c['left_real'])+1j*np.asarray(c['left_imag']),'right':np.asarray(c['right_real'])+1j*np.asarray(c['right_imag']),'omega':float(c['omega']),'frequency':float(c['frequency']),'sigma':float(c['sigma']),'growth_to_omega':float(c['growth_to_omega']),'coordinate_energy_fraction':float(c.get('coordinate_energy_fraction',1)),'eigen_relation_residual':float(c.get('eigen_relation_residual',0)),'discovery_cycles':float(c.get('discovery_cycles',1))}


def analyze_sciii_stage_a(work,cfg):
    work=Path(work); out=work/'analysis'; out.mkdir(parents=True,exist_ok=True); modes_dir=out/'sciii_modes'; modes_dir.mkdir(exist_ok=True); pairs=_pairs(work); eps=float(cfg.get('epsilon_probe',0.02)); disc_t=float(cfg.get('sciii_discovery_time',4.0)); topk=int(cfg.get('sciii_pod_rank',8)); rows=[]; carriers=[]; candidates=[]
    for pid,rr in sorted(pairs.items()):
        rp,rm,r0=_arm(rr,1),_arm(rr,-1),_arm(rr,0); priority=any(bool(r.get('certification_priority',False)) for r in rr); base={'pair_id':pid,'carrier_id':rr[0]['carrier_id'],'topology_group_id':rr[0].get('topology_group_id',''),'provenance_group_id':rr[0].get('provenance_group_id',''),'n_components':int(rr[0].get('n_components',1)),'certification_priority':priority}
        fps=[_stage_a_file(work,r) for r in (rp,rm,r0)] if all((rp,rm,r0)) else []
        if len(fps)!=3 or not all(p.exists() for p in fps): carriers.append({**base,'geometry_ok':False,'status':'MISSING_STAGE_A','n_sciii_candidates':0}); continue
        zp,zm,z0=[np.load(p,allow_pickle=False) for p in fps]; gm=_stage_a_geometry_metrics((zp,zm,z0),cfg)
        if not gm['geometry_ok']: carriers.append({**base,**gm,'status':'GEOMETRY_GATE','n_sciii_candidates':0}); continue
        n=min(len(zp['t']),len(zm['t']),len(z0['t'])); t=np.asarray(z0['t'][:n],float); nd=int(np.searchsorted(t,disc_t,side='right')); nd=max(32,min(n-80,nd))
        if nd>=n-80: carriers.append({**base,**gm,'status':'TOO_SHORT_FOR_SCIII','n_sciii_candidates':0}); continue
        nat,ref=natural_response(_cut(z0,n)); odd,_=odd_response(_cut(zp,n),_cut(zm,n),eps); even=even_probe_contamination(_cut(zp,n),_cut(zm,n),_cut(z0,n)); even_ratio=float(np.sqrt(np.mean(even[:nd]**2))/max(eps*np.sqrt(np.mean(odd[:nd]**2)),1e-15)); ncand=0
        for channel,response in [('natural',nat),('odd',odd)]:
            modes,ev,center=learn_modes(response,nd,topk); amps=project(response,modes,center); Xd=amps[:nd]; Xh=amps[nd:]; th=t[nd:]; disc=_discovery_candidates(t[:nd],Xd,cfg)
            modefile=modes_dir/f'{rp["carrier_id"]}_{channel}.npz'; np.savez_compressed(modefile,pod_modes=modes,pod_energy=ev,center=center,reference=ref,component_offsets=np.asarray(z0['component_offsets'],dtype=np.int64) if 'component_offsets' in z0.files else np.asarray([0,len(ref)],dtype=np.int64),discovery_time=float(t[nd-1]),channel=channel)
            for di,d in enumerate(disc[:int(cfg.get('sciii_max_discovery_complex_modes',4))]):
                met,q,loc=sciii_metrics(th,Xh,d,cfg); q1,q2,q3,q4,q5,q6=sciii_gates(d,met,cfg,channel); cand=bool(gm['geometry_ok'] and q1 and q2 and q3 and q4 and q5 and q6)
                row={**base,**gm,'channel':channel,'dmd_mode_index':di,'mode_file':str(modefile.relative_to(work)),'even_probe_ratio':even_ratio,'SCIII_Q1_discovery_complex_mode':q1,'SCIII_Q2_moving_subspace_continuation':q2,'SCIII_Q3_coherent_complex_phase':q3,'SCIII_Q4_neutral_persistent_amplitude':q4,'SCIII_Q5_local_out_of_sample_prediction':q5,'SCIII_Q6_natural_channel':q6,'sciii_provisional_candidate':cand,**{f'discovery_{k}':v for k,v in _serialize_discovery(d).items() if k not in {'left_real','left_imag','right_real','right_imag'}},**{f'phase_{k}':v for k,v in met.items() if k!='local_windows'}}; rows.append(row)
                if cand:
                    ncand+=1; candidates.append({'pair_id':pid,'carrier_id':rp['carrier_id'],'topology_group_id':rp.get('topology_group_id',''),'provenance_group_id':rp.get('provenance_group_id',''),'n_components':int(rp.get('n_components',1)),'channel':channel,'mode_file':str(modefile.relative_to(work)),'dmd_mode_index':di,'discovery':_serialize_discovery(d),'period':met.get('period'),'frequency':met.get('frequency'),'phase_wraps':met.get('phase_wraps'),'phase_diffusion_rms_rad':met.get('phase_diffusion_rms_rad'),'local_frequency_cv':met.get('local_frequency_cv'),'mode_overlap_median':met.get('mode_overlap_median'),'certification_priority':priority})
        carriers.append({**base,**gm,'status':'VALID','even_probe_ratio':even_ratio,'n_sciii_candidates':ncand})
    _savecsv(out/'blind_sciii_dmd_results.csv',rows); _savecsv(out/'blind_sciii_carrier_summary.csv',carriers); (out/'sciii_candidates_provisional.json').write_text(json.dumps(clean_json({'format':'SST-SCIII-CANDIDATES-PROVISIONAL-1.0','candidates':candidates}),indent=2,sort_keys=True)+'\n'); (out/'sciii_candidates.json').write_text(json.dumps({'format':'SST-SCIII-CANDIDATES-CERTIFIED-1.0','candidates':[]},indent=2)+'\n')
    total=len(carriers); valid=sum(int(r.get('geometry_ok',False)) for r in carriers); ptotal=sum(int(r.get('certification_priority',False)) for r in carriers); pvalid=sum(int(r.get('certification_priority',False) and r.get('geometry_ok',False)) for r in carriers); cov=_coverage_gate(total,valid,ptotal,pvalid,cfg)
    gate='PASS_SCIII_PROVISIONAL_KOOPMAN_DMD_PHASE_CLOCK__REQUIRES_MESH_GAUGE_CERTIFICATION' if candidates else ('FAIL_SCIII_NO_KOOPMAN_DMD_COMPLEX_PHASE_CLOCK' if cov['coverage_ok_for_global_fail'] else 'INDETERMINATE_SCIII_INSUFFICIENT_VALID_COVERAGE')
    summary={'format':'SST-SCIII-KOOPMAN-DMD-STAGE-A-BLIND-1.0','definition':'moving-subspace local Koopman/DMD complex phase with predictive continuation','n_carriers':total,'n_geometry_valid_carriers':valid,'n_dmd_hypotheses_tested':len(rows),'n_sciii_provisional_candidates':len(candidates),'carriers_with_sciii_provisional_candidates':len(set(c['carrier_id'] for c in candidates)),'carrier_identity_read':False,'primary_channel':'natural','odd_channel_role':'diagnostic/null only','discovery_time_absolute':disc_t,**cov,'primary_gate':gate}; (out/'blind_sciii_stage_a_summary.json').write_text(json.dumps(clean_json(summary),indent=2,sort_keys=True)+'\n'); return summary


def _gauge_candidate(work,cfg,c,branch,rr):
    rp,rm,r0=_arm(rr,1),_arm(rr,-1),_arm(rr,0); fps=[_stage_a_file(work,r,branch) for r in (rp,rm,r0)]
    if not all(p.exists() for p in fps): return {'geometry_ok':False,'reason':'MISSING_GAUGE_TRAJECTORY'}
    zp,zm,z0=[np.load(p,allow_pickle=False) for p in fps]; gm=_stage_a_geometry_metrics((zp,zm,z0),cfg)
    if not gm['geometry_ok']: return gm
    mf=np.load(work/c['mode_file'],allow_pickle=False); modes=np.asarray(mf['pod_modes'],float); center=np.asarray(mf['center'],float); n=min(len(z0['t']),len(zp['t']),len(zm['t'])); t=np.asarray(z0['t'][:n],float); nd=int(np.searchsorted(t,float(cfg.get('sciii_discovery_time',4.0)),side='right')); nd=max(32,min(n-80,nd)); nat,_=natural_response(_cut(z0,n)); amps=project(nat,modes,center); d=_deserialize_discovery(c['discovery']); met,_,_=sciii_metrics(t[nd:],amps[nd:],d,cfg); _,q2,q3,q4,q5,q6=sciii_gates(d,met,cfg,'natural'); return {**gm,**met,'sciii_phase_ok':bool(q2 and q3 and q4 and q5 and q6)}


def analyze_sciii_gauge(work,cfg):
    work=Path(work); out=work/'analysis'; provisional=_manifest(work,'sciii_candidates_provisional.json'); pairs=_pairs(work); rows=[]; cert=[]
    for c in provisional:
        rr=pairs.get(c['pair_id'],[]); lo=_gauge_candidate(work,cfg,c,'stage_a_gauge_low',rr); hi=_gauge_candidate(work,cfg,c,'stage_a_gauge_high',rr); pspread=_rel_spread([c.get('period'),lo.get('period'),hi.get('period')]); fspread=_rel_spread([c.get('frequency'),lo.get('frequency'),hi.get('frequency')]); ok=bool(lo.get('geometry_ok') and hi.get('geometry_ok') and lo.get('sciii_phase_ok') and hi.get('sciii_phase_ok') and pspread<=float(cfg.get('sciii_gate_max_mesh_period_spread',0.15)) and fspread<=float(cfg.get('sciii_gate_max_mesh_frequency_spread',0.15))); row={**c,'gauge_low_geometry_ok':lo.get('geometry_ok',False),'gauge_high_geometry_ok':hi.get('geometry_ok',False),'mesh_period_spread':pspread,'mesh_frequency_spread':fspread,'mesh_gauge_invariant':ok}; rows.append(row); cert.append(row) if ok else None
    _savecsv(out/'blind_sciii_gauge_results.csv',rows); (out/'sciii_candidates.json').write_text(json.dumps(clean_json({'format':'SST-SCIII-CANDIDATES-CERTIFIED-1.0','candidates':cert}),indent=2,sort_keys=True)+'\n'); base=json.loads((out/'blind_sciii_stage_a_summary.json').read_text()) if (out/'blind_sciii_stage_a_summary.json').exists() else {}; gate='PASS_SCIII_KOOPMAN_DMD_PHASE_CLOCK_MESH_GAUGE_CERTIFIED' if cert else ('FAIL_OR_INDETERMINATE_SCIII_PROVISIONAL_NOT_MESH_GAUGE_INVARIANT' if provisional else base.get('primary_gate','INDETERMINATE_SCIII_NO_STAGE_A_RESULT')); s={'format':'SST-SCIII-MESH-GAUGE-BLIND-1.0','n_provisional_candidates':len(provisional),'n_mesh_gauge_certified_candidates':len(cert),'carrier_identity_read':False,'primary_gate':gate}; (out/'blind_sciii_gauge_summary.json').write_text(json.dumps(clean_json(s),indent=2,sort_keys=True)+'\n'); return s


def analyze_sciii_provenance(work,cfg):
    work=Path(work); out=work/'analysis'; catalog=load_catalog(work); cert=_manifest(work,'sciii_candidates.json'); meta={}
    for r in catalog: meta.setdefault(r['carrier_id'],{'topology_group_id':r.get('topology_group_id',''),'provenance_group_id':r.get('provenance_group_id','')})
    bytop={}; certby={}
    for cid,m in meta.items(): bytop.setdefault(m['topology_group_id'],{}).setdefault(m['provenance_group_id'],[]).append(cid)
    for c in cert: certby.setdefault(c['carrier_id'],[]).append(c)
    rows=[]; robust=0
    for top,fams in sorted(bytop.items()):
        fam=[]; periods=[]
        for _,cids in fams.items():
            cc=[x for cid in cids for x in certby.get(cid,[])]; fam.append(bool(cc)); periods += [float(np.median([x['period'] for x in cc]))] if cc else []
        frac=sum(fam)/max(len(fam),1); spread=_rel_spread(periods); ok=bool(sum(fam)>=int(cfg.get('sciii_gate_min_provenance_source_families',2)) and frac>=float(cfg.get('sciii_gate_min_provenance_fraction',2/3)) and spread<=float(cfg.get('sciii_gate_max_provenance_period_spread',0.30))); robust+=int(ok); rows.append({'topology_group_id':top,'n_source_families_available':len(fams),'n_source_families_with_sciii_clock':sum(fam),'source_family_candidate_fraction':frac,'period_spread':spread,'provenance_robust_sciii_clock':ok})
    _savecsv(out/'blind_sciii_provenance_results.csv',rows); stage=json.loads((out/'blind_sciii_stage_a_summary.json').read_text()) if (out/'blind_sciii_stage_a_summary.json').exists() else {}; gate='PASS_SCIII_PROVENANCE_ROBUST_KOOPMAN_DMD_PHASE_CLOCK' if robust else ('PASS_SCIII_SEED_SPECIFIC_CLOCK__PROVENANCE_NOT_ROBUST' if cert else stage.get('primary_gate','INDETERMINATE_SCIII_NO_STAGE_A_RESULT')); status=gate if robust else ('SCIII_CERTIFIED_CLOCK_NOT_PROVENANCE_ROBUST' if cert else 'NOT_REACHED_NO_CERTIFIED_SCIII_CANDIDATE'); s={'format':'SST-SCIII-PROVENANCE-BLIND-1.0','n_groups_with_provenance_robust_sciii_clock':robust,'n_certified_sciii_candidates':len(cert),'carrier_identity_read':False,'overall_primary_gate':gate,'provenance_status':status,'primary_gate':gate}; (out/'blind_sciii_provenance_summary.json').write_text(json.dumps(clean_json(s),indent=2,sort_keys=True)+'\n'); return s


def analyze_sciii_stage_b(work,cfg):
    work=Path(work); out=work/'analysis'; cert=_manifest(work,'sciii_candidates.json'); pairs=_pairs(work); rows=[]
    for c in cert:
        rr=pairs.get(c['pair_id'],[]); rp,rm,r0=_arm(rr,1),_arm(rr,-1),_arm(rr,0)
        if not all((rp,rm,r0)): continue
        mf=np.load(work/c['mode_file'],allow_pickle=False); pod=np.asarray(mf['pod_modes'],float); center=np.asarray(mf['center'],float); ref=np.asarray(mf['reference'],float); offs=np.asarray(mf['component_offsets'],dtype=np.int64); d=_deserialize_discovery(c['discovery']); spatial=np.tensordot(d['right'],pod,axes=(0,0)); wr=mode_strain_weights(spatial.real,ref,offs); wi=mode_strain_weights(spatial.imag,ref,offs); met={}; missing=False
        for branch in ('material','fixed'):
            fps=[_stage_b_file(work,branch,r) for r in (rp,rm,r0)]
            if not all(p.exists() for p in fps): missing=True; break
            zp,zm,z0=[np.load(p,allow_pickle=False) for p in fps]; n=min(len(zp['t']),len(zm['t']),len(z0['t'])); t=np.asarray(z0['t'][:n],float); nat,_=natural_response(_cut(z0,n)); amps=project(nat,pod,center); q=amps@d['left']; ph=np.unwrap(np.angle(q)); sr=np.asarray(z0['sigma'][:n])@wr; si=np.asarray(z0['sigma'][:n])@wi; stan=-np.sin(ph)*sr+np.cos(ph)*si; geom=bool(float(t[-1])>=float(cfg.get('stage_b_discovery_time',0.8))+float(cfg.get('sciii_stage_b_min_periods_observed',1.25))*float(c.get('period') or 1) and float(np.max(z0['ds_cv']))<=float(cfg.get('stage_b_hard_ds_cv',0.45))); met[branch]={'geometry_ok':geom,'actual_t_final':float(t[-1]),'max_ds_cv':float(np.max(z0['ds_cv'])),**(delayed_pair_phase_modulation_test(t,q.real,q.imag,stan,float(c.get('period') or 1),cfg) if geom else {})}
        if missing: continue
        md,fd=met['material'],met['fixed']; b1=bool(md.get('geometry_ok') and abs(md.get('holdout_corr',0))>=float(cfg.get('sciii_gate_min_stretch_phase_corr',0.30)) and md.get('phase_null_p',1)<=float(cfg.get('gate_max_phase_null_p',0.10))); b2=bool(b1 and md.get('delay_advantage_abs_corr',-99)>=float(cfg.get('gate_min_delay_advantage',0.05))); b3=bool(b2 and (not fd.get('geometry_ok') or abs(md.get('holdout_corr',0))-abs(fd.get('holdout_corr',0))>=float(cfg.get('gate_min_material_over_fixed_corr',0.08)))); rows.append({**c,**{f'material_{k}':v for k,v in md.items()},**{f'fixed_{k}':v for k,v in fd.items()},'SCIII_B1_stretch_phase_modulation':b1,'SCIII_B2_delay_advantage':b2,'SCIII_B3_material_specificity':b3,'sciii_mechanism_candidate':b3})
    _savecsv(out/'blind_sciii_stage_b_results.csv',rows); mech=[r for r in rows if r.get('sciii_mechanism_candidate')]; stage=json.loads((out/'blind_sciii_stage_a_summary.json').read_text()) if (out/'blind_sciii_stage_a_summary.json').exists() else {}; gauge=json.loads((out/'blind_sciii_gauge_summary.json').read_text()) if (out/'blind_sciii_gauge_summary.json').exists() else {}; prov=json.loads((out/'blind_sciii_provenance_summary.json').read_text()) if (out/'blind_sciii_provenance_summary.json').exists() else {}; provisional=_manifest(work,'sciii_candidates_provisional.json')
    if mech: gate='PASS_SCIII_KOOPMAN_DMD_PHASE_CLOCK_MECHANISM'; sb='PASS_SCIII_KOOPMAN_DMD_PHASE_CLOCK_MECHANISM'
    elif cert: gate='PASS_SCIII_KOOPMAN_DMD_PHASE_CLOCK__FAIL_OR_INDETERMINATE_CAUSAL_MECHANISM'; sb='FAIL_OR_INDETERMINATE_CAUSAL_MECHANISM'
    else: gate=stage.get('primary_gate') or gauge.get('primary_gate') or prov.get('primary_gate') or 'INDETERMINATE_SCIII_NO_STAGE_A_RESULT'; sb='NOT_REACHED_NO_CERTIFIED_SCIII_CANDIDATE'
    s={'format':'SST-SCIII-KOOPMAN-DMD-COMPLEX-PHASE-CLOCK-BLIND-1.0','n_sciii_certified_candidates':len(cert),'n_stage_b_results':len(rows),'n_sciii_mechanism_candidates':len(mech),'stage_a_gate':stage.get('primary_gate'),'mesh_gauge_gate':gauge.get('primary_gate'),'provenance_gate':prov.get('primary_gate'),'stage_a_candidate_status':'SCIII_PROVISIONAL_KOOPMAN_DMD_CLOCK_FOUND' if provisional else 'NO_SCIII_PROVISIONAL_KOOPMAN_DMD_CLOCK','mesh_gauge_status':'SCIII_MESH_GAUGE_CERTIFIED_CANDIDATE_EXISTS' if cert else ('NO_SCIII_MESH_GAUGE_CERTIFIED_CANDIDATE' if provisional else 'NOT_REACHED_NO_PROVISIONAL_SCIII_CANDIDATE'),'provenance_status':prov.get('provenance_status') or ('NOT_REACHED_NO_CERTIFIED_SCIII_CANDIDATE' if not cert else prov.get('primary_gate')),'stage_b_status':sb,'carrier_identity_read':False,'moving_subspace_continuation':True,'overall_primary_gate':gate,'primary_gate':gate}; (out/'blind_sciii_summary.json').write_text(json.dumps(clean_json(s),indent=2,sort_keys=True)+'\n'); return s
