from __future__ import annotations
from pathlib import Path
from typing import Any
import csv, itertools, json, math, os
import numpy as np
from .common import *
from .geometry import load_geometry, biot_savart_probe, fibonacci_sphere, frame_holonomy, relative_norm

FEATURES=['ACN','kappa_rms','tau_rms','dcsd','ropelength','Wr']


def _write_csv(path:Path,rows:list[dict[str,Any]]):
    path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys:keys.append(k)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)


def _base(phase_id:str,slug:str,advisory:list[str],root:Path)->dict[str,Any]:
    return {'schema':'A056-PHASE-RESULT-1','phase_id':phase_id,'slug':slug,'nonblocking':True,'advisory_dependencies':advisory_state(advisory,root),'source_archive':verify_source_archive(root)}


def p00(root:Path,out:Path)->dict[str,Any]:
    r=_base('P00','SOURCE_INTAKE',[],root)
    src=r['source_archive']
    if not src['pass']:
        r.update(status='UNRESOLVED',evidence_class='SOURCE_INVALID',reason='Frozen E011 archive missing or SHA mismatch.');return r
    run=atlas_json('RUN_SUMMARY.json',root);sel=atlas_json('SELECTION.json',root);idx=atlas_csv('STATIC_READY_INDEX.csv',root)
    rows=[]
    for x in idx:
        rows.append({'candidate_id':opaque_topology(x['topology_id'],root),'static_ready':x['static_ready']=='True','static_status':x['static_status'],'primary_seed_count':int(x['primary_seed_count']),'primary_provider_count':int(x['primary_provider_count']),'provider_anchor_count':int(x['provider_anchor_count'])})
    _write_csv(out/'ANONYMOUS_ATLAS_INDEX.csv',rows)
    knot_count=sum(1 for t in sel.get('topology_ids',[]) if not t.startswith('L'))
    link_count=len(sel.get('topology_ids',[]))-knot_count
    checks={
      'atlas_schema':run.get('schema')=='E011-SKLSA-STATIC-READY-ATLAS-1',
      'execution_gate':run.get('execution_gate')=='PASS',
      'operational_errors_zero':run.get('operational_error_count')==0,
      'selected_count_match':len(sel.get('topology_ids',[]))==run.get('selected_topology_count'),
      'prime_knots_through_8_present_count':knot_count==35,
      'static_ready_count_match':sum(x['static_ready']=='True' for x in idx)==run.get('static_ready_topology_count')
    }
    status='PASS' if all(checks.values()) else 'FAIL'
    r.update(status=status,evidence_class='STATIC_SOURCE_QUALIFIED' if status=='PASS' else 'STATIC_SOURCE_INCONSISTENT',checks=checks,metrics={'selected_anonymous_objects':len(rows),'anonymous_knot_objects':knot_count,'anonymous_link_objects':link_count,'static_ready_objects':run.get('static_ready_topology_count'),'cross_provider_robust_objects':run.get('cross_provider_robust_topology_count'),'cross_provider_sensitive_objects':run.get('cross_provider_sensitive_topology_count')},scientific_boundary=run.get('scientific_boundary'))
    return r


def _matrix(root:Path):
    agg=provider_aggregates(root); ids=sorted(agg)
    # only static-ready objects with >=4 usable features
    keep=[];X=[];miss=[]
    for tid in ids:
        a=agg[tid]
        vals=[a['metrics'].get(m) for m in FEATURES]
        n=sum(v is not None for v in vals)
        if a['static_ready'] and n>=4:
            keep.append(tid);X.append([np.nan if v is None else float(v) for v in vals]);miss.append(len(FEATURES)-n)
    X=np.asarray(X,float); Z,med,scale=robust_z(X)
    return agg,keep,X,Z,med,scale,miss


def p01(root:Path,out:Path)->dict[str,Any]:
    r=_base('P01','STATIC_STRUCTURE',['P00'],root)
    if not r['source_archive']['pass']:
        r.update(status='UNRESOLVED',evidence_class='SOURCE_INVALID');return r
    agg,ids,X,Z,med,scale,miss=_matrix(root)
    U,S,Vt=np.linalg.svd(Z-Z.mean(0),full_matrices=False)
    coords=U[:,:min(3,U.shape[1])]*S[:min(3,len(S))]
    cluster_trials=[]
    for k in range(2,min(7,len(ids))):
        lab,C,iner=kmeans(Z,k); sil=silhouette(Z,lab)
        cluster_trials.append((k,lab,sil,iner))
    best=max(cluster_trials,key=lambda q:(-999 if math.isnan(q[2]) else q[2]))
    k,labels,sil,iner=best
    rows=[]
    for i,tid in enumerate(ids):
        row={'candidate_id':opaque_topology(tid,root),'cluster':int(labels[i]),'static_status':agg[tid]['static_status'],'provider_count':len(agg[tid]['providers']),'missing_features':miss[i]}
        for j,m in enumerate(FEATURES):row[m]=None if not np.isfinite(X[i,j]) else float(X[i,j])
        for j in range(coords.shape[1]):row[f'PC{j+1}']=float(coords[i,j])
        rows.append(row)
    _write_csv(out/'ANONYMOUS_FEATURE_SPACE.csv',rows)
    D=np.sqrt(((Z[:,None,:]-Z[None,:,:])**2).sum(2))
    np.save(out/'ANONYMOUS_DISTANCE_MATRIX.npy',D)
    write_json(out/'CLUSTER_DIAGNOSTICS.json',{'best_k':k,'silhouette':sil,'inertia':iner,'trials':[{'k':a,'silhouette':b,'inertia':c} for a,_l,b,c in cluster_trials],'feature_order':FEATURES,'robust_center':med.tolist(),'robust_scale':scale.tolist(),'candidate_order':[opaque_topology(t,root) for t in ids]})
    checks={'enough_objects':len(ids)>=20,'feature_dimension':Z.shape[1]>=5,'finite_matrix':bool(np.isfinite(Z).all()),'nontrivial_structure':bool(not math.isnan(sil) and sil>=0.12)}
    # Discovery can FAIL without blocking later phases.
    status='PASS' if all(checks.values()) else 'FAIL'
    r.update(status=status,evidence_class='TARGET_FREE_STATIC_STRUCTURE',checks=checks,metrics={'object_count':len(ids),'feature_count':Z.shape[1],'best_k':k,'best_silhouette':sil,'pc1_fraction':float(S[0]**2/max((S**2).sum(),1e-30))})
    return r


def p02(root:Path,out:Path)->dict[str,Any]:
    r=_base('P02','CONJUGATION',['P00','P01'],root)
    if not r['source_archive']['pass']:
        r.update(status='UNRESOLVED',evidence_class='SOURCE_INVALID');return r
    agg=provider_aggregates(root)
    # Static algebraic lane: registered candidate amplitudes are even geometry scalars; state sign s is independent.
    static=[]
    for tid,a in agg.items():
        if not a['static_ready']:continue
        wr=a['metrics'].get('Wr');acn=a['metrics'].get('ACN')
        if wr is None or acn in (None,0):continue
        amp=abs(float(wr))/max(abs(float(acn)),1e-12)
        static.append({'candidate_id':opaque_topology(tid,root),'amplitude_abs_wr_over_acn':amp,'q_plus':amp,'q_minus':-amp,'oddness_error':0.0})
    _write_csv(out/'CONJUGATION_STATIC_CANDIDATES.csv',static)
    # Optional numerical filament lane using provenance-resolved KnotPlot VECT/XYZ anchors.
    workbench=Path(os.environ.get('SST_WORKBENCH_ROOT',r'C:\workspace\projects\SST-Workbench'))
    anchors=atlas_jsonl('STATIC_READY_PROVIDER_ANCHORS.jsonl',root)
    dyn=[]; max_odd=0.; max_even=0.
    for a in anchors:
        loc=a.get('source_locator',{})
        if loc.get('representation') not in {'vect','xyz'}:continue
        comps,why=load_geometry(loc,workbench)
        if comps is None:continue
        # knots only; multi-component sources are deferred to composite phase
        if len(comps)!=1:continue
        P=comps[0]; P=P-P.mean(0); radius=max(np.linalg.norm(P,axis=1).max()*3.5,1.0)
        probes=fibonacci_sphere(72,radius)
        vp=biot_savart_probe(P,+1.0,probes);vm=biot_savart_probe(P,-1.0,probes)
        odd=float(np.linalg.norm(vp+vm)/max(np.linalg.norm(vp),1e-30))
        ep=float(np.mean(np.sum(vp*vp,axis=1)));em=float(np.mean(np.sum(vm*vm,axis=1)))
        even=abs(ep-em)/max(abs(ep),abs(em),1e-30)
        max_odd=max(max_odd,odd);max_even=max(max_even,even)
        dyn.append({'candidate_id':opaque_topology(a['topology_id'],root),'provider_group':a.get('provider_group'),'representation':loc.get('representation'),'velocity_oddness_error':odd,'energy_evenness_error':even,'probe_energy_plus':ep,'probe_energy_minus':em})
    _write_csv(out/'FILAMENT_CONJUGATION_PARITY.csv',dyn)
    static_pass=len(static)>=20
    dyn_available=len(dyn)>=6
    dyn_pass=dyn_available and max(max_odd,max_even)<=1e-11
    if not static_pass:status='FAIL';ec='STATIC_CONJUGATION_INSUFFICIENT'
    elif dyn_available and dyn_pass:status='PASS';ec='NUMERICAL_CONJUGATION_COVARIANCE'
    elif dyn_available:status='FAIL';ec='NUMERICAL_CONJUGATION_BROKEN'
    else:status='UNRESOLVED';ec='STATIC_IDENTITY_ONLY_DYNAMIC_SOURCE_UNAVAILABLE'
    r.update(status=status,evidence_class=ec,checks={'static_candidate_lane':static_pass,'dynamic_geometry_lane_available':dyn_available,'dynamic_odd_even_covariance':dyn_pass if dyn_available else None},metrics={'static_candidate_count':len(static),'dynamic_geometry_count':len(dyn),'max_velocity_oddness_error':max_odd if dyn else None,'max_energy_evenness_error':max_even if dyn else None},interpretation_guard='Sign reversal of a circulation-linear field with an even quadratic energy is a conjugation symmetry candidate only; it does not identify a physical anti-state or electric charge.')
    return r


def _response_amplitudes(a:dict[str,Any])->dict[str,float]:
    m=a['metrics'];wr=m.get('Wr');acn=m.get('ACN');rop=m.get('ropelength')
    if wr is None:return {}
    w=abs(float(wr));o={'ABS_WR':w}
    if acn not in (None,0):
        A=abs(float(acn));o['ABS_WR_OVER_ACN']=w/max(A,1e-12);o['ABS_WR_OVER_1PLUS_ACN']=w/(1+A)
    if rop not in (None,0):o['ABS_WR_OVER_ROPELENGTH']=w/max(abs(float(rop)),1e-12)
    return o


def p03(root:Path,out:Path)->dict[str,Any]:
    r=_base('P03','SIGNED_RESPONSE',['P01','P02'],root)
    if not r['source_archive']['pass']:
        r.update(status='UNRESOLVED',evidence_class='SOURCE_INVALID');return r
    agg=provider_aggregates(root)
    # candidate knots only; links have IDs beginning L in E011 source, but blind outputs retain opaque IDs only.
    tids=[t for t,a in agg.items() if a['static_ready'] and not t.startswith('L')]
    rankings=[]
    for obs in ['ABS_WR','ABS_WR_OVER_ACN','ABS_WR_OVER_1PLUS_ACN','ABS_WR_OVER_ROPELENGTH']:
        vals={t:_response_amplitudes(agg[t]).get(obs) for t in tids};vals={t:v for t,v in vals.items() if v is not None and v>1e-10}
        local=[]
        for A,B in itertools.combinations(sorted(vals),2):
            a,b=vals[A],vals[B]
            # Search discrete relative sign; 3-component multiplicities are preregistered 2+1 / 1+2, not semantic labels.
            best=None
            for s in (-1.0,1.0):
                qa=a;qb=s*b
                c1=abs(2*qa+qb);c2=abs(qa+2*qb)
                if c1<=c2:cancel=c1;which='2A+B';comp=abs(qa+2*qb)
                else:cancel=c2;which='A+2B';comp=abs(2*qa+qb)
                score=cancel/max(3*max(a,b),1e-12)
                item=(score,-comp, s,which,cancel,comp)
                if best is None or item<best:best=item
            score,negcomp,s,which,cancel,comp=best
            # provider robustness uses amplitude spread as a penalty, not pseudo-replication.
            sp=max(agg[A]['relative_spread'].get('Wr',0.0),agg[B]['relative_spread'].get('Wr',0.0))
            penal=score+0.10*min(sp,5.0)
            local.append({'observable':obs,'candidate_A':opaque_topology(A,root),'candidate_B':opaque_topology(B,root),'relative_sign_B':int(s),'canceling_composition':which,'cancellation_score':score,'companion_amplitude':comp,'provider_wr_spread_max':sp,'penalized_score':penal})
        local.sort(key=lambda x:(x['penalized_score'],x['cancellation_score'],-x['companion_amplitude']))
        for rank,x in enumerate(local[:30],1):x['rank']=rank;rankings.append(x)
    _write_csv(out/'PAIR_DISCOVERY_RANKING.csv',rankings)
    top=[x for x in rankings if x['rank']==1]
    robust=[x for x in rankings if x['cancellation_score']<=0.08 and x['provider_wr_spread_max']<=0.25 and x['companion_amplitude']>1e-6]
    status='PASS' if robust else 'FAIL'
    r.update(status=status,evidence_class='TARGET_FREE_ADDITIVE_RESPONSE_DISCOVERY',checks={'ranking_nonempty':bool(rankings),'provider_robust_cancellation_candidate':bool(robust)},metrics={'ranking_rows':len(rankings),'qualified_pair_rows':len(robust),'best_by_observable':top},interpretation_guard='These are dimensionless signed-response candidates with a free discrete state sign. No row is an electric-charge measurement until an independent physical coupling operator is supplied.')
    return r


def p04(root:Path,out:Path)->dict[str,Any]:
    r=_base('P04','MONODROMY',['P00','P01'],root)
    # Universal SO(3) lift is an analytic control, intentionally not evidence of particle spin.
    q2=np.array([math.cos(math.pi),0,0,math.sin(math.pi)])
    q4=np.array([math.cos(2*math.pi),0,0,math.sin(2*math.pi)])
    universal={'q_2pi':q2.tolist(),'q_4pi':q4.tolist(),'two_pi_minus_identity_error':float(np.linalg.norm(q2-np.array([-1.,0,0,0]))),'four_pi_identity_error':float(np.linalg.norm(q4-np.array([1.,0,0,0])))}
    write_json(out/'SO3_DOUBLE_COVER_CONTROL.json',universal)
    workbench=Path(os.environ.get('SST_WORKBENCH_ROOT',r'C:\workspace\projects\SST-Workbench'))
    anchors=atlas_jsonl('STATIC_READY_PROVIDER_ANCHORS.jsonl',root) if r['source_archive']['pass'] else []
    rows=[]
    for a in anchors:
        loc=a.get('source_locator',{})
        if loc.get('representation') not in {'vect','xyz'}:continue
        comps,why=load_geometry(loc,workbench)
        if comps is None or len(comps)!=1:continue
        try:h=frame_holonomy(comps[0])
        except Exception:continue
        rows.append({'candidate_id':opaque_topology(a['topology_id'],root),'provider_group':a.get('provider_group'),'frame_holonomy_rad':h,'frame_holonomy_turns':h/(2*math.pi),'distance_to_half_turn':abs(abs(h)/(2*math.pi)-0.5)})
    _write_csv(out/'FRAME_HOLONOMY.csv',rows)
    # Knot-specific gate requires provider-repeated holonomy and actual variation beyond numerical noise.
    by={}
    for x in rows:by.setdefault(x['candidate_id'],[]).append(x['frame_holonomy_turns'])
    repeated=[v for v in by.values() if len(v)>=2]
    spread=float(np.std([np.median(v) for v in repeated])) if repeated else 0.0
    knot_specific=len(repeated)>=3 and spread>=1e-3
    status='PASS' if knot_specific else ('UNRESOLVED' if len(rows)<6 else 'FAIL')
    r.update(status=status,evidence_class='KNOT_SPECIFIC_FRAME_HOLONOMY' if knot_specific else 'UNIVERSAL_DOUBLE_COVER_ONLY',checks={'universal_4pi_control':universal['four_pi_identity_error']<1e-12,'knot_geometry_holonomy_available':len(rows)>=6,'provider_repeated_knot_holonomy':len(repeated)>=3,'topology_dependent_variation':knot_specific},metrics={'holonomy_rows':len(rows),'provider_repeated_objects':len(repeated),'median_holonomy_between_object_std':spread},interpretation_guard='The 2pi/4pi quaternion lift is universal to SO(3) and cannot certify quantum spin. Only an additional topology-dependent state-space monodromy can become a spin candidate.')
    return r


def p05(root:Path,out:Path)->dict[str,Any]:
    r=_base('P05','INVOLUTIONS',['P02','P03','P04'],root)
    if not r['source_archive']['pass']:
        r.update(status='UNRESOLVED',evidence_class='SOURCE_INVALID');return r
    agg=provider_aggregates(root)
    rows=[]
    for tid,a in agg.items():
        if not a['static_ready']:continue
        wr=a['metrics'].get('Wr');acn=a['metrics'].get('ACN')
        if wr is None or acn in (None,0):continue
        amp=abs(float(wr))/max(abs(float(acn)),1e-12)
        # Three mathematically distinct involutions are explicitly kept distinct.
        rows += [
          {'candidate_id':opaque_topology(tid,root),'involution':'CIRCULATION_SIGN','geometry_changed':False,'curve_orientation_changed':False,'state_sign_changed':True,'mass_proxy_parity':'EVEN','signed_response_parity':'ODD','candidate_eigenvalue':0.5},
          {'candidate_id':opaque_topology(tid,root),'involution':'CURVE_ORIENTATION','geometry_changed':False,'curve_orientation_changed':True,'state_sign_changed':False,'mass_proxy_parity':'EVEN','signed_response_parity':'MODEL_DEPENDENT','candidate_eigenvalue':None},
          {'candidate_id':opaque_topology(tid,root),'involution':'SPATIAL_MIRROR','geometry_changed':True,'curve_orientation_changed':False,'state_sign_changed':False,'mass_proxy_parity':'EVEN_EXPECTED','signed_response_parity':'OBSERVABLE_DEPENDENT','candidate_eigenvalue':None},
        ]
    _write_csv(out/'INVOLUTION_CENSUS.csv',rows)
    p02r=load_phase_result('P02',root);p04r=load_phase_result('P04',root)
    independent=(p02r is not None and p02r.get('status')=='PASS' and p04r is not None and p04r.get('status')=='PASS')
    # Do not award PASS just because a binary sign was defined; need an independent topology-dependent lane.
    status='PASS' if independent else 'FAIL'
    r.update(status=status,evidence_class='MULTI_INVOLUTION_TWO_STATE_STRUCTURE' if independent else 'DEFINED_BINARY_STATE_WITHOUT_INDEPENDENT_COUPLING',checks={'circulation_involution_registered':bool(rows),'independent_topology_dependent_monodromy':bool(p04r and p04r.get('status')=='PASS'),'circulation_covariance_certified':bool(p02r and p02r.get('status')=='PASS'),'nondegenerate_two_state_support':independent},metrics={'involution_rows':len(rows)},interpretation_guard='Assigning +/-1/2 to a binary involution is normalization, not a derivation of a weak generator. PASS requires a second, independently measured topology-dependent structure.')
    return r


def p06(root:Path,out:Path)->dict[str,Any]:
    r=_base('P06','U1_CLOSURE',['P03','P04','P05'],root)
    p03r=load_phase_result('P03',root);p04r=load_phase_result('P04',root);p05r=load_phase_result('P05',root)
    independent=bool(p04r and p04r.get('status')=='PASS' and p05r and p05r.get('status')=='PASS')
    diag={'independent_second_observable_available':independent,'definition_guard':'The second U1-like observable may not be defined as 2*(Q-T3).','closure_attempted':False}
    if not independent:
        write_json(out/'U1_CLOSURE_DIAGNOSTIC.json',diag)
        r.update(status='UNRESOLVED',evidence_class='NO_INDEPENDENT_SECOND_U1_OBSERVABLE',checks={'independent_second_observable':False,'heldout_closure':None},metrics=diag,interpretation_guard='Closure is intentionally not computed from a definitionally constructed quantity.')
        return r
    # If independent frame holonomy exists, join it to the best signed-response amplitude and perform a label-free held-out linear relation diagnostic.
    hpath=phase_dir('P04',root)/'FRAME_HOLONOMY.csv';qpath=phase_dir('P03',root)/'PAIR_DISCOVERY_RANKING.csv'
    # This version does not manufacture per-state Q values from pair rankings; keep hard gate unresolved rather than overfit.
    diag.update({'closure_attempted':False,'reason':'v0.1.0 has independent frame holonomy but no independently calibrated per-object signed coupling; fitting one here would conflate discovery and calibration.'})
    write_json(out/'U1_CLOSURE_DIAGNOSTIC.json',diag)
    r.update(status='UNRESOLVED',evidence_class='INDEPENDENT_PHASE_AVAILABLE_BUT_Q_OPERATOR_UNCALIBRATED',checks={'independent_second_observable':True,'heldout_closure':None},metrics=diag,interpretation_guard='A later version may preregister a calibration/held-out split, but v0.1.0 does not retrofit one after seeing data.')
    return r


def p07(root:Path,out:Path)->dict[str,Any]:
    r=_base('P07','COMPOSITES',['P03','P05','P06'],root)
    if not r['source_archive']['pass']:
        r.update(status='UNRESOLVED',evidence_class='SOURCE_INVALID');return r
    pair_file=phase_dir('P03',root)/'PAIR_DISCOVERY_RANKING.csv'
    pairs=[]
    if pair_file.is_file():
        with pair_file.open(encoding='utf-8-sig') as f:pairs=list(csv.DictReader(f))
    top=[]
    for x in pairs:
        if int(x['rank'])<=5:
            top.append({'candidate_A':x['candidate_A'],'candidate_B':x['candidate_B'],'observable':x['observable'],'relative_sign_B':int(x['relative_sign_B']),'canceling_composition':x['canceling_composition'],'cancellation_score':float(x['cancellation_score']),'companion_amplitude':float(x['companion_amplitude'])})
    _write_csv(out/'THREE_COMPONENT_ADDITIVE_CANDIDATES.csv',top)
    idx={x['topology_id']:x for x in atlas_csv('STATIC_READY_INDEX.csv',root)}
    # Anonymous architecture readiness counts; exact source topology IDs are not emitted blind.
    link_rows=[x for t,x in idx.items() if t.startswith('L')]
    static_links=sum(x['static_ready']=='True' for x in link_rows)
    # The selected atlas contains the canonical 3-component Brunnian control but it is not STATIC_READY in v0.3.0.
    brunnian_ready=idx.get('L6a4',{}).get('static_ready')=='True'
    architecture={'link_objects_selected':len(link_rows),'link_objects_static_ready':static_links,'three_component_brunnian_control_static_ready':brunnian_ready,'synthetic_trivial_loop_control':'AVAILABLE_ANALYTICALLY','open_connector_control':'STRUCTURAL_ONLY_ENDPOINT_BOUNDARY_REQUIRED'}
    write_json(out/'ARCHITECTURE_READINESS.json',architecture)
    additive=any(x['cancellation_score']<=0.08 for x in top)
    # Full mechanism PASS requires both additive discovery and a source-qualified three-component container. It is expected to remain unresolved if E011 lacks it.
    if additive and brunnian_ready:status='PASS';ec='ADDITIVE_PLUS_ARCHITECTURE_QUALIFIED'
    elif additive:status='UNRESOLVED';ec='ADDITIVE_CANDIDATE_CONTAINER_NOT_STATIC_READY'
    else:status='FAIL';ec='NO_ADDITIVE_CANDIDATE'
    r.update(status=status,evidence_class=ec,checks={'additive_three_component_candidate':additive,'three_component_container_static_ready':brunnian_ready,'connector_controls_available':static_links>0},metrics=architecture|{'top_additive_rows':len(top)},interpretation_guard='Additive cancellation does not establish binding. Container/connector topology and finite-core dynamics must be qualified independently.')
    return r

PHASES={'P00':p00,'P01':p01,'P02':p02,'P03':p03,'P04':p04,'P05':p05,'P06':p06,'P07':p07}
