from __future__ import annotations
from pathlib import Path
import csv,json,math,statistics
import numpy as np
from .seal import verify

def p_ge(k,n):return float(sum(math.comb(n,j) for j in range(k,n+1))/(2**n)) if n else 1.0

def _load_case(blind,cid):return json.loads((Path(blind)/'cases'/f'{cid}.json').read_text())
def reveal(project_root,blind,catalog,config,private,outdir):
    verify(project_root,blind,catalog,config,private);blind=Path(blind);private=Path(private);out=Path(outdir);out.mkdir(parents=True,exist_ok=True)
    cand={r['candidate_id']:r for r in csv.DictReader(open(private/'candidate_key.csv',encoding='utf-8'))};pkey={r['pair_id']:r for r in csv.DictReader(open(private/'pair_key.csv',encoding='utf-8'))};brows=list(csv.DictReader(open(blind/'blind_pair_results.csv',encoding='utf-8')));rows=[]
    for r in brows:
        k=pkey[r['pair_id']];ca,cb=r['candidate_a'],r['candidate_b'];A,B=cand[ca],cand[cb];active=k['candidate_active'];null=k['candidate_null'];win=r['winner_anonymous'];winner=ca if win=='A' else cb if win=='B' else win.lower();med=float(r['median_log_ratio_A_over_B']) if r['median_log_ratio_A_over_B'] not in ('',None,'None') else float('nan');effect=med if ca==active else -med
        ra, rn = _load_case(blind,active), _load_case(blind,null)
        rows.append({**r,'carrier_id':k['carrier_id'],'family':k['family'],'beta':float(k['beta']),'gamma_core':float(k['gamma_core']),'n_threads':int(k['n_threads']),'helix_turns':float(k['helix_turns']),'winner_condition':'active' if winner==active else 'null' if winner==null else winner,'log_ratio_active_over_null':effect,'pressure_delta_active_minus_null':float(ra.get('pressure_center_minus_shell',np.nan)-rn.get('pressure_center_minus_shell',np.nan)),'active_pressure_center_minus_shell':float(ra.get('pressure_center_minus_shell',np.nan)),'null_pressure_center_minus_shell':float(rn.get('pressure_center_minus_shell',np.nan)),'active_r2_1_over_r':float(ra.get('r2_1_over_r',np.nan)),'active_r2_1_over_r2':float(ra.get('r2_1_over_r2',np.nan)),'active_r2_advantage_1_over_r':float(ra.get('r2_advantage_1_over_r',np.nan)),'active_restoring_fraction':float(ra.get('restoring_fraction',np.nan)),'null_restoring_fraction':float(rn.get('restoring_fraction',np.nan))})
    fields=list(rows[0]) if rows else ['pair_id']
    with open(out/'revealed_pairs.csv','w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    alpha=json.loads(Path(config).read_text()).get('reveal_alpha',0.05);families={}
    for fam in sorted(set(r['family'] for r in rows)):
        rr=[r for r in rows if r['family']==fam and r['winner_condition'] in ('active','null')];aw=sum(r['winner_condition']=='active' for r in rr);nw=len(rr)-aw;effects=[r['log_ratio_active_over_null'] for r in rr if np.isfinite(r['log_ratio_active_over_null'])];med=float(statistics.median(effects)) if effects else float('nan');pa=p_ge(aw,len(rr));pn=p_ge(nw,len(rr))
        if len(rr) and pa<=alpha and med<0:verdict='SUPPORTS_THREADED_SELF_CONFINEMENT'
        elif len(rr) and pn<=alpha and med>0:verdict='FALSIFIES_THREADED_SELF_CONFINEMENT'
        else:verdict='INDETERMINATE'
        families[fam]={'n_non_ties':len(rr),'active_wins':aw,'null_wins':nw,'one_sided_p_active':pa,'median_log_ratio_active_over_null':med,'median_ratio_active_over_null':float(math.exp(med)) if np.isfinite(med) else float('nan'),'verdict':verdict}
    pr=[r for r in rows if np.isfinite(r['pressure_delta_active_minus_null'])];pd=sum(r['pressure_delta_active_minus_null']<0 for r in pr);pp=p_ge(pd,len(pr));medpd=float(statistics.median([r['pressure_delta_active_minus_null'] for r in pr])) if pr else float('nan')
    grav=[r for r in rows if np.isfinite(r['active_r2_advantage_1_over_r'])];gwin=sum(r['active_r2_advantage_1_over_r']>0 for r in grav);gp=p_ge(gwin,len(grav));medg=float(statistics.median([r['active_r2_advantage_1_over_r'] for r in grav])) if grav else float('nan')
    if pr and pp<=alpha and medpd<0:pressure_status='SUPPORTS_THREAD_DENSITY_PRESSURE_DEFICIT'
    else:pressure_status='INDETERMINATE_PRESSURE_DEFICIT'
    if grav and gp<=alpha and medg>0:profile_status='SUPPORTS_1_OVER_R_OVER_1_OVER_R2'
    elif grav and p_ge(len(grav)-gwin,len(grav))<=alpha and medg<0:profile_status='FAVORS_1_OVER_R2_NOT_NEWTONIAN'
    else:profile_status='INDETERMINATE_FAR_PROFILE'
    if pressure_status.startswith('SUPPORTS') and profile_status.startswith('SUPPORTS'):gravity='CANDIDATE_GRAVITY_CLOSURE_SURVIVES_THIS_GATE'
    elif pressure_status.startswith('SUPPORTS'):gravity='PRESSURE_DEFICIT_ONLY_GRAVITY_NOT_CLOSED'
    else:gravity='GRAVITY_CLOSURE_NOT_SUPPORTED'
    # Euler circulation-similarity: after tau = |Gamma_K| t, dimensionless outcomes should be gamma-independent at fixed other parameters.
    sim_groups={}
    for r in rows:sim_groups.setdefault((r['carrier_id'],r['beta'],r['n_threads'],r['helix_turns']),[]).append(r)
    cvs=[]
    for key,rr in sim_groups.items():
        if len({x['gamma_core'] for x in rr})<2:continue
        vals=[]
        for x in rr:
            case=_load_case(blind,pkey[x['pair_id']]['candidate_active']);vals.append(float(case['final_shape_distance']))
        m=np.mean(vals);cvs.append(float(np.std(vals)/max(abs(m),1e-12)))
    medcv=float(statistics.median(cvs)) if cvs else float('nan');sim_status='PASS_EULER_CIRCULATION_SIMILARITY' if cvs and medcv<=0.08 else ('FAIL_CIRCULATION_SIMILARITY' if cvs and medcv>=0.20 else 'INDETERMINATE_CIRCULATION_SIMILARITY')
    summary={'seal_verified':True,'family_self_confinement':families,'pressure_gate':{'n':len(pr),'active_more_negative':pd,'one_sided_p':pp,'median_pressure_delta_active_minus_null':medpd,'status':pressure_status},'far_field_profile_gate':{'n':len(grav),'one_over_r_better':gwin,'one_sided_p':gp,'median_r2_advantage_1_over_r':medg,'status':profile_status},'gravity_closure':gravity,'circulation_similarity':{'n_groups':len(cvs),'median_cv_final_shape_distance':medcv,'status':sim_status},'triple_gear_note':'The T(3,3) carrier is a three-unknot-link topology proxy. Mechanical tooth/helix transmission is not used by blind scoring.','interpretation_guard':'Self-confinement, central pressure deficit, and Newton-like far-field profile are independent gates. Passing one does not imply the others.'}
    (out/'REVEAL_SUMMARY.json').write_text(json.dumps(summary,indent=2,sort_keys=True,allow_nan=True)+'\n')
    lines=['# SST Threaded-Hole Substrate — post-seal reveal','','Seal verification: **PASS**.','','## Self-confinement']
    for fam,x in families.items():lines.append(f"- `{fam}`: **{x['verdict']}** — active {x['active_wins']}/{x['n_non_ties']} non-ties, p={x['one_sided_p_active']:.6g}, median active/null ratio={x['median_ratio_active_over_null']:.6g}.")
    lines += ['', '## Pressure / gravity',f"- Pressure deficit: **{pressure_status}**, p={pp:.6g}, median Δp(active-null)={medpd:.6g}.",f"- Far profile: **{profile_status}**, p={gp:.6g}, median ΔR²(1/r - 1/r²)={medg:.6g}.",f"- Combined gravity closure: **{gravity}**.",'', '## Circulation similarity',f"- **{sim_status}**, median CV={medcv:.6g}.",'','No gear ratio, SST constant, Newton target value, carrier family or active/null identity entered the blind scorer.']
    (out/'CONCLUSIONS.md').write_text('\n'.join(lines)+'\n');return summary
