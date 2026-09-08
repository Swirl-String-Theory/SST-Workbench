from __future__ import annotations
from pathlib import Path
import csv,json,math,statistics
from collections import defaultdict
import numpy as np
from .seal import verify
from .stats import exact_sign_p_ge,carrier_cluster,polynomial_pressure_law,symmetric_even_odd
from .pressure import fit_free_power_exponent


def _load_case(blind,cid):return json.loads((Path(blind)/'cases'/f'{cid}.json').read_text(encoding='utf-8'))

def _f(x,default=float('nan')):
    try:return float(x)
    except Exception:return default


def _delta_profile_fit(ra,rn,cfg):
    rr=np.asarray(ra.get('radial_r',[]),float);rp=np.asarray(ra.get('radial_p',[]),float);nr=np.asarray(rn.get('radial_r',[]),float);np0=np.asarray(rn.get('radial_p',[]),float)
    if len(rr)<4 or len(rr)!=len(rp) or len(rr)!=len(nr) or len(rr)!=len(np0) or not np.allclose(rr,nr,rtol=1e-8,atol=1e-10):
        return {'nu_best':float('nan'),'r2_best':float('nan'),'coeff':float('nan'),'boundary_hit':True}
    fitcfg=cfg.get('pressure_fit',{})
    return fit_free_power_exponent(rr,rp-np0,float(fitcfg.get('nu_min',.10)),float(fitcfg.get('nu_max',4.0)),int(fitcfg.get('nu_steps',157)))

def _delta_ladder_fit(ra,rn,cfg):
    al=ra.get('pressure_convergence',{}).get('levels',[]) if isinstance(ra.get('pressure_convergence',{}),dict) else []
    nl=rn.get('pressure_convergence',{}).get('levels',[]) if isinstance(rn.get('pressure_convergence',{}),dict) else []
    vals=[];rows=[]
    for a,b in zip(al,nl):
        f=_delta_profile_fit(a,b,cfg);rows.append({'grid_n':a.get('grid_n'),'box_half':a.get('box_half'),**f})
        if np.isfinite(f['nu_best']) and not f['boundary_hit']:vals.append(float(f['nu_best']))
    return {'levels':rows,'n_levels':len(rows),'nu_median':float(np.median(vals)) if vals else float('nan'),'nu_span':float(np.ptp(vals)) if len(vals)>1 else 0.0 if len(vals)==1 else float('nan')}

def _winner_condition(win,ca,cb,active,null):
    if win=='A':w=ca
    elif win=='B':w=cb
    else:return str(win).lower()
    return 'active' if w==active else 'null' if w==null else 'unknown'

def _condition_vote(x):return -1 if x=='active' else 1 if x=='null' else 0

def _family_cluster(rows,alpha):
    out={}
    for fam in sorted(set(r['family'] for r in rows)):
        rr=[r for r in rows if r['winner_condition'] in ('active','null') and r.get('decision_mode','self_confinement')=='self_confinement' and r['analysis_mode']!='pressure_only']
        rr=[r for r in rr if r['family']==fam]
        by=defaultdict(list)
        for r in rr:by[r['carrier_id']].append(_condition_vote(r['winner_condition']))
        carrier_votes={cid:int(np.sign(np.median(v))) for cid,v in by.items() if v}
        # vote=-1 is active favorable
        aw=sum(v<0 for v in carrier_votes.values());nw=sum(v>0 for v in carrier_votes.values());n=aw+nw;pa=exact_sign_p_ge(aw,n);pn=exact_sign_p_ge(nw,n)
        effects=[r['log_ratio_active_over_null'] for r in rr if np.isfinite(r['log_ratio_active_over_null']) and r['decision_basis']=='FULL_HORIZON_PRIMARY_METRICS']
        med=float(np.median(effects)) if effects else float('nan')
        verdict='SUPPORTS_THREADED_SELF_CONFINEMENT' if n and pa<=alpha and aw>nw else 'FALSIFIES_THREADED_SELF_CONFINEMENT' if n and pn<=alpha and nw>aw else 'INDETERMINATE'
        out[fam]={'n_conditions_non_tie':len(rr),'condition_active_wins':sum(r['winner_condition']=='active' for r in rr),'condition_null_wins':sum(r['winner_condition']=='null' for r in rr),'n_carriers_non_tie':n,'carrier_active_wins':aw,'carrier_null_wins':nw,'carrier_votes':carrier_votes,'one_sided_p_active_carrier_cluster':pa,'one_sided_p_null_carrier_cluster':pn,'median_log_ratio_full_horizon_only':med,'median_ratio_full_horizon_only':float(math.exp(med)) if np.isfinite(med) else float('nan'),'verdict':verdict}
    return out

def reveal(project_root,blind,catalog,config,private,outdir):
    verify(project_root,blind,catalog,config,private);blind=Path(blind);private=Path(private);out=Path(outdir);out.mkdir(parents=True,exist_ok=True);cfg=json.loads(Path(config).read_text(encoding='utf-8'));alpha=float(cfg.get('reveal_alpha',.05))
    cand={r['candidate_id']:r for r in csv.DictReader(open(private/'candidate_key.csv',encoding='utf-8'))};pkey={r['pair_id']:r for r in csv.DictReader(open(private/'pair_key.csv',encoding='utf-8'))};brows=list(csv.DictReader(open(blind/'blind_pair_results.csv',encoding='utf-8')));rows=[]
    for r in brows:
        k=pkey[r['pair_id']];ca,cb=r['candidate_a'],r['candidate_b'];active=k['candidate_active'];null=k['candidate_null'];win=r['winner_anonymous'];winner=_winner_condition(win,ca,cb,active,null);med=_f(r.get('median_log_ratio_A_over_B'));effect=med if ca==active else -med if np.isfinite(med) or np.isinf(med) else float('nan');ra,rn=_load_case(blind,active),_load_case(blind,null)
        pdelta=_f(ra.get('pressure_center_minus_shell'))-_f(rn.get('pressure_center_minus_shell'))
        dprof={'nu_best':_f(r.get('delta_far_profile_nu_blind')),'r2_best':_f(r.get('delta_far_profile_r2_blind')),'coeff':_f(r.get('delta_far_profile_coeff_A_minus_B_blind')),'boundary_hit':str(r.get('delta_far_profile_boundary_hit_blind','')).lower()=='true'}
        dconv={'n_levels':int(_f(r.get('delta_pressure_ladder_n_blind'),0)),'nu_span':_f(r.get('delta_pressure_ladder_nu_span_blind')),'monopole_rel_span':_f(r.get('delta_pressure_ladder_monopole_rel_span_blind'))}
        dq_ab=_f(r.get('delta_source_monopole_A_minus_B_blind'));dq=dq_ab if ca==active else -dq_ab
        coeff_ab=_f(r.get('delta_far_profile_coeff_A_minus_B_blind'));dcoeff=coeff_ab if ca==active else -coeff_ab
        aph=ra.get('phase_lock',{}) if isinstance(ra.get('phase_lock',{}),dict) else {};nph=rn.get('phase_lock',{}) if isinstance(rn.get('phase_lock',{}),dict) else {}
        rows.append({**r,'carrier_id':k['carrier_id'],'family':k['family'],'beta_parameter':_f(k.get('beta_parameter')),'beta_total_thread_over_core':_f(k.get('beta_total_thread_over_core')),'thread_coupling_mode':k.get('thread_coupling_mode','total_beta'),'campaign_role':k.get('campaign_role','general'),'gamma_core':_f(k['gamma_core']),'n_threads':int(k['n_threads']),'helix_turns':_f(k['helix_turns']),'winner_condition':winner,'log_ratio_active_over_null':effect,'analysis_mode':ra.get('analysis_mode','full'),'decision_mode':str(cfg.get('decision_mode','self_confinement')).lower(),'active_dynamic_status':ra.get('dynamic_status',''),'null_dynamic_status':rn.get('dynamic_status',''),'active_actual_tau_end':_f(ra.get('actual_tau_end')),'null_actual_tau_end':_f(rn.get('actual_tau_end')),'pressure_delta_active_minus_null':pdelta,'delta_source_monopole_active_minus_null':dq,'delta_source_monopole_fraction_abs':_f(r.get('delta_source_monopole_fraction_abs_blind')),'delta_far_profile_coeff_active_minus_null':dcoeff,'active_pressure_center_minus_shell':_f(ra.get('pressure_center_minus_shell')),'null_pressure_center_minus_shell':_f(rn.get('pressure_center_minus_shell')),'active_far_profile_nu_best':_f(ra.get('far_profile_nu_best')),'active_far_profile_r2_best':_f(ra.get('far_profile_r2_best')),'active_far_profile_coeff_best':_f(ra.get('far_profile_coeff_best')),'active_far_profile_nu_boundary_hit':bool(ra.get('far_profile_nu_boundary_hit',False)),'delta_far_profile_nu_best':_f(dprof.get('nu_best')),'delta_far_profile_r2_best':_f(dprof.get('r2_best')),'delta_far_profile_coeff_best':_f(dprof.get('coeff')),'delta_far_profile_nu_boundary_hit':bool(dprof.get('boundary_hit',True)),'active_r2_1_over_r':_f(ra.get('r2_1_over_r')),'active_r2_1_over_r2':_f(ra.get('r2_1_over_r2')),'active_r2_advantage_1_over_r':_f(ra.get('r2_advantage_1_over_r')),'delta_pressure_ladder_n':int(dconv.get('n_levels',0) or 0),'delta_pressure_ladder_nu_median':_f(dconv.get('nu_median')),'delta_pressure_ladder_nu_span':_f(dconv.get('nu_span')),'delta_pressure_ladder_monopole_rel_span':_f(dconv.get('monopole_rel_span')),'active_thread_density_log_growth':_f(ra.get('thread_density_log_growth')),'null_thread_density_log_growth':_f(rn.get('thread_density_log_growth')),'thread_density_growth_active_minus_null':_f(ra.get('thread_density_log_growth'))-_f(rn.get('thread_density_log_growth')),'active_restoring_fraction':_f(ra.get('restoring_fraction')),'null_restoring_fraction':_f(rn.get('restoring_fraction')),'active_max_real_growth':_f(ra.get('max_real_growth')),'null_max_real_growth':_f(rn.get('max_real_growth')),'active_gear_phase_lock_score':_f(aph.get('gear_phase_lock_score')),'null_gear_phase_lock_score':_f(nph.get('gear_phase_lock_score')),'active_best_rational_p':aph.get('best_rational_p'),'active_best_rational_q':aph.get('best_rational_q'),'active_thread_over_carrier_rate':_f(aph.get('thread_over_carrier_rate'))})
    fields=list(rows[0]) if rows else ['pair_id']
    with open(out/'revealed_pairs.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

    families=_family_cluster(rows,alpha)
    all_dyn=[r for r in rows if r['winner_condition'] in ('active','null') and r.get('decision_mode','self_confinement')=='self_confinement' and r['analysis_mode']!='pressure_only'];by=defaultdict(list)
    for r in all_dyn:by[r['carrier_id']].append(_condition_vote(r['winner_condition']))
    cvotes={cid:int(np.sign(np.median(v))) for cid,v in by.items()};aw=sum(v<0 for v in cvotes.values());nw=sum(v>0 for v in cvotes.values());n=aw+nw;self_cluster={'carrier_votes':cvotes,'n_carriers_non_tie':n,'carrier_active_wins':aw,'carrier_null_wins':nw,'one_sided_p_active':exact_sign_p_ge(aw,n),'one_sided_p_null':exact_sign_p_ge(nw,n)}
    if n and self_cluster['one_sided_p_active']<=alpha and aw>nw:self_status='SUPPORTS_THREADED_SELF_CONFINEMENT'
    elif n and self_cluster['one_sided_p_null']<=alpha and nw>aw:self_status='FALSIFIES_THREADED_SELF_CONFINEMENT'
    else:self_status='INDETERMINATE'
    self_cluster['status']=self_status

    # Carrier-clustered pressure gate: the independent experimental unit is the carrier, not beta.
    pr=[r for r in rows if np.isfinite(r['pressure_delta_active_minus_null'])]
    pcl=carrier_cluster([r['pressure_delta_active_minus_null'] for r in pr],[r['carrier_id'] for r in pr],True);pressure_status='SUPPORTS_THREAD_DENSITY_PRESSURE_DEFICIT' if pcl['n_nonzero_carriers'] and pcl['one_sided_exact_sign_p']<=alpha and pcl['median_of_carrier_medians']<0 else 'INDETERMINATE_PRESSURE_DEFICIT'
    pressure_gate={**pcl,'status':pressure_status,'n_conditions':len(pr)}

    # Pressure law per carrier.  This is most informative in preset_pressure_law.
    law_rows=[]
    for cid in sorted(set(r['carrier_id'] for r in pr)):
        rr=[r for r in pr if r['carrier_id']==cid];b=[r['beta_total_thread_over_core'] for r in rr];y=[r['pressure_delta_active_minus_null'] for r in rr];poly=polynomial_pressure_law(b,y,int(cfg.get('pressure_law_degree',4)));sym=symmetric_even_odd(b,y);law_rows.append({'carrier_id':cid,'family':rr[0]['family'],'n':len(rr),'poly_r2':poly['r2'],'c1_A':poly['coefficients'][0] if len(poly['coefficients'])>0 else float('nan'),'c2_B':poly['coefficients'][1] if len(poly['coefficients'])>1 else float('nan'),'c3_C':poly['coefficients'][2] if len(poly['coefficients'])>2 else float('nan'),'c4_D':poly['coefficients'][3] if len(poly['coefficients'])>3 else float('nan'),'median_even_quadratic_B':sym['median_even_quadratic_B'],'median_odd_linear_A':sym['median_odd_linear_A'],'n_symmetric_pairs':sym['n_symmetric_pairs']})
    with open(out/'pressure_law.csv','w',newline='',encoding='utf-8') as f:
        fs=list(law_rows[0]) if law_rows else ['carrier_id'];w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(law_rows)
    bvals=[r['median_even_quadratic_B'] for r in law_rows if np.isfinite(r['median_even_quadratic_B'])];bneg=sum(x<0 for x in bvals);pressure_law_gate={'n_carriers_with_symmetric_pairs':len(bvals),'B_negative_carriers':bneg,'one_sided_p_B_negative':exact_sign_p_ge(bneg,len(bvals)) if bvals else 1.0,'median_B':float(np.median(bvals)) if bvals else float('nan'),'status':'SUPPORTS_NEGATIVE_EVEN_QUADRATIC_THREAD_PRESSURE' if bvals and exact_sign_p_ge(bneg,len(bvals))<=alpha and np.median(bvals)<0 else 'INDETERMINATE_PRESSURE_LAW'}

    # Free-space gravity closure: pressure deficit + source monopole + asymptotic exponent + two convergence gates.
    target=float(cfg.get('gravity_exponent_target',1.0));alt=float(cfg.get('gravity_exponent_alternative',2.0));tol=float(cfg.get('gravity_exponent_tolerance',.25));minr2=float(cfg.get('gravity_min_profile_r2',.75))
    grav=[r for r in rows if np.isfinite(r['delta_far_profile_nu_best']) and np.isfinite(r['delta_far_profile_r2_best']) and r['delta_far_profile_r2_best']>=minr2 and not r['delta_far_profile_nu_boundary_hit']]
    gby=defaultdict(list)
    for r in grav:gby[r['carrier_id']].append(r['delta_far_profile_nu_best'])
    gmed={k:float(np.median(v)) for k,v in gby.items()};closer=sum(abs(v-target)<abs(v-alt) for v in gmed.values());far_n=len(gmed);pcloser=exact_sign_p_ge(closer,far_n);within=sum(abs(v-target)<=tol for v in gmed.values());median_nu=float(np.median(list(gmed.values()))) if gmed else float('nan')
    exponent_status='SUPPORTS_NEWTON_LIKE_FREE_EXPONENT' if far_n and pcloser<=alpha and abs(median_nu-target)<=tol else 'INDETERMINATE_FREE_EXPONENT'
    exponent_gate={'carrier_median_nu':gmed,'n_carriers':far_n,'closer_to_target_than_alternative':closer,'one_sided_p_closer':pcloser,'within_target_tolerance':within,'target_nu_post_reveal':target,'alternative_nu_post_reveal':alt,'tolerance':tol,'median_carrier_nu':median_nu,'min_r2_inclusion':minr2,'status':exponent_status}

    # Positive induced source monopole Q_delta is required for delta p ~ -Q/(4 pi r).
    min_mfrac=float(cfg.get('gravity_min_monopole_fraction_abs',.01));mr=[r for r in rows if np.isfinite(r['delta_source_monopole_active_minus_null']) and np.isfinite(r['delta_source_monopole_fraction_abs']) and r['delta_source_monopole_fraction_abs']>=min_mfrac];mby=defaultdict(list)
    for r in mr:mby[r['carrier_id']].append(r['delta_source_monopole_active_minus_null'])
    mmed={k:float(np.median(v)) for k,v in mby.items()};mpos=sum(v>0 for v in mmed.values());mn=len(mmed);mp=exact_sign_p_ge(mpos,mn) if mn else 1.0;monopole_status='SUPPORTS_NEGATIVE_1_OVER_R_MONOPOLE_SIGN' if mn and mp<=alpha and np.median(list(mmed.values()))>0 else 'INDETERMINATE_OR_WRONG_MONOPOLE'
    monopole_gate={'carrier_median_Q_delta':mmed,'n_carriers':mn,'positive_Q_carriers':mpos,'one_sided_p':mp,'min_abs_fraction':min_mfrac,'status':monopole_status}

    ladder=[r for r in rows if r['delta_pressure_ladder_n']>=2];span_tol=float(cfg.get('pressure_ladder_nu_span_tolerance',.25));qspan_tol=float(cfg.get('pressure_ladder_monopole_rel_span_tolerance',.25));lby=defaultdict(list);qby=defaultdict(list)
    for r in ladder:
        if np.isfinite(r['delta_pressure_ladder_nu_span']):lby[r['carrier_id']].append(r['delta_pressure_ladder_nu_span'])
        if np.isfinite(r['delta_pressure_ladder_monopole_rel_span']):qby[r['carrier_id']].append(r['delta_pressure_ladder_monopole_rel_span'])
    lmed={k:float(np.median(v)) for k,v in lby.items()};qmed={k:float(np.median(v)) for k,v in qby.items()};conv=sum(v<=span_tol for v in lmed.values());ln=len(lmed);qconv=sum(v<=qspan_tol for v in qmed.values());qn=len(qmed);pconv=exact_sign_p_ge(conv,ln) if ln else 1.;pqconv=exact_sign_p_ge(qconv,qn) if qn else 1.;conv_status='PASS_FAR_FIELD_CONVERGENCE' if ln and pconv<=alpha and conv>ln/2 else 'NEEDS_OR_FAILS_FAR_FIELD_CONVERGENCE';qconv_status='PASS_MONOPOLE_CONVERGENCE' if qn and pqconv<=alpha and qconv>qn/2 else 'NEEDS_OR_FAILS_MONOPOLE_CONVERGENCE'
    convergence_gate={'carrier_median_nu_span':lmed,'n_carriers':ln,'converged_carriers':conv,'span_tolerance':span_tol,'one_sided_p':pconv,'status':conv_status,'carrier_median_monopole_rel_span':qmed,'monopole_n_carriers':qn,'monopole_converged_carriers':qconv,'monopole_span_tolerance':qspan_tol,'monopole_one_sided_p':pqconv,'monopole_status':qconv_status}
    if pressure_status.startswith('SUPPORTS') and monopole_status.startswith('SUPPORTS') and exponent_status.startswith('SUPPORTS') and conv_status.startswith('PASS') and qconv_status.startswith('PASS'):gravity='CANDIDATE_GRAVITY_CLOSURE_SURVIVES_V0_2_1_GATE'
    elif pressure_status.startswith('SUPPORTS'):gravity='PRESSURE_DEFICIT_SUPPORTED_GRAVITY_CLOSURE_NOT_CLOSED'
    else:gravity='GRAVITY_CLOSURE_NOT_SUPPORTED'

    # Dynamic thread focusing: active threads versus identical zero-circulation passive tracers.
    foc=[r for r in rows if np.isfinite(r.get('thread_density_growth_active_minus_null',np.nan))];fcl=carrier_cluster([-r['thread_density_growth_active_minus_null'] for r in foc],[r['carrier_id'] for r in foc],True) if foc else {'n_nonzero_carriers':0,'one_sided_exact_sign_p':1.0,'median_of_carrier_medians':float('nan')}
    # carrier_cluster expects negative favorable; using -delta makes active density growth > null favorable.
    focusing_status='SUPPORTS_DYNAMIC_THREAD_FOCUSING' if foc and fcl.get('one_sided_exact_sign_p',1.0)<=alpha and fcl.get('median_of_carrier_medians',0)<0 else 'INDETERMINATE_THREAD_FOCUSING'
    focusing_gate={**fcl,'n_conditions':len(foc),'status':focusing_status}

    # Fresh preregistered confirmatory stability conditions are evaluated separately from discovery scans.
    conf=[r for r in rows if r.get('campaign_role')=='confirmatory_stability'];confirmatory={'n_pairs':len(conf),'active_wins':sum(r['winner_condition']=='active' for r in conf),'null_wins':sum(r['winner_condition']=='null' for r in conf),'ties':sum(r['winner_condition'] not in ('active','null') for r in conf),'status':'CONFIRMATORY_ACTIVE_DOMINANT' if conf and sum(r['winner_condition']=='active' for r in conf)>sum(r['winner_condition']=='null' for r in conf) else 'CONFIRMATORY_NOT_ESTABLISHED'}

    # Euler circulation similarity.
    sim_groups=defaultdict(list)
    for r in rows:sim_groups[(r['carrier_id'],r['beta_total_thread_over_core'],r['n_threads'],r['helix_turns'])].append(r)
    cvs=[]
    for key,rr in sim_groups.items():
        if len({x['gamma_core'] for x in rr})<2:continue
        vals=[]
        for x in rr:
            case=_load_case(blind,pkey[x['pair_id']]['candidate_active'])
            if case.get('dynamic_status')=='PASS_FULL_HORIZON' and np.isfinite(_f(case.get('final_shape_distance'))):vals.append(_f(case['final_shape_distance']))
        if len(vals)>=2:cvs.append(float(np.std(vals)/max(abs(np.mean(vals)),1e-12)))
    medcv=float(np.median(cvs)) if cvs else float('nan');sim_status='PASS_EULER_CIRCULATION_SIMILARITY' if cvs and medcv<=float(cfg.get('similarity_cv_pass',.08)) else ('FAIL_CIRCULATION_SIMILARITY' if cvs and medcv>=float(cfg.get('similarity_cv_fail',.20)) else 'INDETERMINATE_CIRCULATION_SIMILARITY')

    # Discovery-only stability islands. Selecting the best scanned condition is not confirmatory inference.
    islands=[]
    for cid in sorted(set(r['carrier_id'] for r in rows)):
        rr=[r for r in rows if r['carrier_id']==cid and r['decision_basis']=='FULL_HORIZON_PRIMARY_METRICS' and np.isfinite(r['log_ratio_active_over_null'])]
        if not rr:continue
        best=min(rr,key=lambda x:x['log_ratio_active_over_null']);islands.append({'carrier_id':cid,'family':best['family'],'best_beta_total':best['beta_total_thread_over_core'],'best_beta_parameter':best['beta_parameter'],'best_n_threads':best['n_threads'],'best_helix_turns':best['helix_turns'],'best_gamma_core':best['gamma_core'],'best_log_ratio_active_over_null':best['log_ratio_active_over_null'],'best_ratio_active_over_null':float(math.exp(best['log_ratio_active_over_null'])),'discovery_only':True})
    with open(out/'stability_islands_discovery.csv','w',newline='',encoding='utf-8') as f:
        fs=list(islands[0]) if islands else ['carrier_id'];w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(islands)

    # Triple-gear geometric phase-lock proxy; no preselected ratio is tested.
    gear=[]
    for r in rows:
        if r['family']!='triple_gear' or not np.isfinite(r['active_gear_phase_lock_score']):continue
        gear.append({'carrier_id':r['carrier_id'],'beta_total':r['beta_total_thread_over_core'],'n_threads':r['n_threads'],'helix_turns':r['helix_turns'],'active_score':r['active_gear_phase_lock_score'],'null_score':r['null_gear_phase_lock_score'],'active_minus_null':r['active_gear_phase_lock_score']-r['null_gear_phase_lock_score'],'best_p':r['active_best_rational_p'],'best_q':r['active_best_rational_q'],'thread_over_carrier_rate':r['active_thread_over_carrier_rate']})
    with open(out/'triple_gear_phase_lock.csv','w',newline='',encoding='utf-8') as f:
        fs=list(gear[0]) if gear else ['carrier_id'];w=csv.DictWriter(f,fieldnames=fs);w.writeheader();w.writerows(gear)
    gear_better=sum(g['active_minus_null']<0 for g in gear if np.isfinite(g['active_minus_null']));gear_gate={'n_conditions':len(gear),'active_lower_phase_lock_score':gear_better,'note':'v0.3.0 retains the v0.2.1 marker-invariant toroidal/poloidal + helix phase; best small rational p/q is discovered, not supplied as a target'}

    hole_gate=None
    if bool(cfg.get('hole_gate_enabled',False)) or str(cfg.get('analysis_mode','')).lower() in ('hole_only','hole_transport'):
        from .hole_reveal import reveal_hole
        hole_gate=reveal_hole(blind,private,cfg,out)

    summary={'campaign_format':'SST-THREADED-HOLE-REVEAL-3.0','seal_verified':True,'self_confinement_carrier_cluster':self_cluster,'family_self_confinement':families,'pressure_gate_carrier_cluster':pressure_gate,'pressure_law_gate':pressure_law_gate,'source_monopole_gate_carrier_cluster':monopole_gate,'free_exponent_gate_carrier_cluster':exponent_gate,'far_field_convergence_gate':convergence_gate,'gravity_closure':gravity,'thread_focusing_gate':focusing_gate,'confirmatory_stability':confirmatory,'circulation_similarity':{'n_groups':len(cvs),'median_cv_final_shape_distance':medcv,'status':sim_status},'stability_islands':{'n_carriers':len(islands),'status':'DISCOVERY_ONLY_REQUIRES_CONFIRMATION'},'triple_gear_phase_lock':gear_gate,'kelvin_threaded_hole_gate':hole_gate,'interpretation_guard':'Self-confinement, dynamic focusing, pressure deficit, source monopole, free-space exponent, convergence, and gear phase locking are independent gates. Pressure deficit alone never closes gravity.'}
    (out/'REVEAL_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True,allow_nan=True)+'\n',encoding='utf-8')
    lines=['# SST Threaded-Hole Substrate v0.3.0 — post-seal reveal','','Seal verification: **PASS**.','','## Self-confinement',f"- Carrier-clustered verdict: **{self_status}** — active carriers {aw}, null carriers {nw}.",'','## Pressure / gravity',f"- Central pressure: **{pressure_status}**.",f"- Even quadratic pressure law: **{pressure_law_gate['status']}**.",f"- Source monopole: **{monopole_status}**.",f"- Free exponent: **{exponent_status}**, median ν={median_nu:.6g}.",f"- Exponent convergence: **{conv_status}**; monopole convergence: **{qconv_status}**.",f"- Combined: **{gravity}**.",'','## Thread focusing',f"- **{focusing_status}** from active versus passive zero-circulation tracer threads.",'','## Confirmatory stability',f"- **{confirmatory['status']}** across {confirmatory['n_pairs']} preregistered pairs.",'','## Stability discovery',f"- {len(islands)} carrier minima reported as discovery only.",'','## Triple gear',f"- Geometric marker-invariant phase proxy available for {len(gear)} conditions; active score lower in {gear_better}. No gear ratio was supplied.",'','Zero-circulation ghost threads are excluded from contact and CFL gates. v0.3.0 additionally tests whether the central hole is a persistent Lagrangian transport structure rather than a visual centerline gap.']
    if hole_gate is not None:
        lines.extend(['','## Kelvin--M\'Farlane central-hole dynamics',f"- **{hole_gate.get('status','INDETERMINATE')}**.",'- Detailed post-seal results: `HOLE_REVEAL_SUMMARY.json`, `hole_revealed_pairs.csv`, `HOLE_CONCLUSIONS.md`.'])
    (out/'CONCLUSIONS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');return summary
