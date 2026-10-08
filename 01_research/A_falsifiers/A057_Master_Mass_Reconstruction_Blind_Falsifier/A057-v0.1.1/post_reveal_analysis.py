from __future__ import annotations
from pathlib import Path
import json,math,statistics
from master_mass.utils import write_json
from master_mass.constants import SST

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'Master_Mass_Reconstruction_Blind_Falsifier_v0.1.1-outputs'
if not (OUT/'REVEAL_VERIFICATION.json').is_file():
    raise SystemExit('Run framework REVEAL or REVEAL_IF_ALLOWED successfully first.')
if not (OUT/'PREDICTIONS_FROZEN.json').is_file():
    raise SystemExit('Missing frozen blind predictions.')
reveal=json.loads((OUT/'revealed'/'reveal.json').read_text(encoding='utf-8'))
pred=json.loads((OUT/'PREDICTIONS_FROZEN.json').read_text(encoding='utf-8'))
res={
 'schema':'A057-POST-REVEAL-ANALYSIS-2',
 'rule':'All compared blind values must already exist in PREDICTIONS_FROZEN.json or another blind output. No post-reveal fitting except the preregistered single-anchor scale lane.',
 'absolute_si':{},'single_anchor':{},'historical_factorized_baseline':{},'rosetta_exposure_sweep':{},'spectral_target':{},'coherence_target':{},'closure_status':{}
}

def cmp(predicted,observed):
    predicted=float(predicted);observed=float(observed)
    return {'predicted_kg':predicted,'observed_kg':observed,'ratio':predicted/observed,'relative_error':abs(predicted-observed)/observed,'log_error':math.log(predicted/observed)}

# 1) Frozen absolute SI lanes: direct line Hamiltonian and universal clock-impedance variant.
for key,target in reveal.get('mass_targets',{}).items():
    source=pred['topologies'].get(target['id']) if target.get('kind')=='topology' else pred['anonymous_composites'].get(target['id'])
    if not source:
        res['absolute_si'][key]={'status':'NOT_FROZEN_PRE_REVEAL'};continue
    obs=float(target['mass_kg']); rr={}
    for lane,pv in source.items():
        if lane.startswith('si_mass_') and isinstance(pv,(int,float)) and pv>0: rr[lane]=cmp(pv,obs)
    res['absolute_si'][key]=rr

# 2) Exactly one observed anchor fixes one global scale; all other registered mappings are predictions.
anchor=reveal['mass_targets']['anchor']; arow=pred['topologies'].get(anchor['id'])
if arow and arow.get('lambda_energy',0)>0:
    scale=float(anchor['mass_kg'])/float(arow['lambda_energy'])
    rr={'anchor_id':anchor['id'],'kg_per_lambda':scale,'predictions':{}}
    for key,target in reveal['mass_targets'].items():
        source=pred['topologies'].get(target['id']) if target.get('kind')=='topology' else pred['anonymous_composites'].get(target['id'])
        if not source: rr['predictions'][key]={'status':'NOT_FROZEN_PRE_REVEAL'};continue
        lam=source.get('lambda_energy',source.get('additive_lambda'))
        if lam is None: rr['predictions'][key]={'status':'NO_FROZEN_LAMBDA'};continue
        rr['predictions'][key]=cmp(scale*float(lam),float(target['mass_kg']))
    res['single_anchor']=rr
else:
    res['single_anchor']={'status':'ANCHOR_NOT_FROZEN_PRE_REVEAL'}

# 3) Historical factorized composite baseline, evaluated exactly from protected preregistered parameters.
hp=reveal.get('historical_model_parameters',{})
if hp:
    base=hp['suppression_base']; alpha=hp['alpha']; n=hp['component_count']; s=hp['tension_index']; m=hp['thread_multiplicity']
    torus_volume=hp['canonical_torus_volume_factor']*SST.r_c**3
    core_mass_per_unit=(0.5*SST.rho_core*SST.v_swirl**2)*torus_volume/SST.c**2
    common=(4.0/alpha)*(m**(-1.5))*(n**(-1.0/base))*(base**(-s))*core_mass_per_unit
    va=2*hp['topological_volume_5_2']+hp['topological_volume_6_1']
    vb=hp['topological_volume_5_2']+2*hp['topological_volume_6_1']
    vals={'assembly_A':common*va,'assembly_B':common*vb}
    for key,pv in vals.items():
        obs=float(reveal['mass_targets'][key]['mass_kg']);res['historical_factorized_baseline'][key]=cmp(pv,obs)
    res['historical_factorized_baseline']['parameters_used']={'component_count':n,'tension_index':s,'thread_multiplicity':m,'geometric_exposure':4.0/alpha,'suppression_base':base}

# 4) Rosetta-style binary geometric-exposure sweep.  G=0 and G=1 are both
# preregistered possibilities; neither is selected from the observed error.
if hp:
    exposure=float(hp['geometric_exposure_G1'])
    for key,target in reveal.get('mass_targets',{}).items():
        source=pred['topologies'].get(target['id']) if target.get('kind')=='topology' else pred['anonymous_composites'].get(target['id'])
        if not source or not source.get('si_mass_core_clock_kg'):
            res['rosetta_exposure_sweep'][key]={'status':'NOT_FROZEN_PRE_REVEAL'};continue
        base=float(source['si_mass_core_clock_kg']);obs=float(target['mass_kg'])
        res['rosetta_exposure_sweep'][key]={'G0':cmp(base,obs),'G1':cmp(base*exposure,obs),'exposure_factor':exposure,'selection_rule':'REPORT_BOTH_NO_POST_REVEAL_SELECTION'}

# 5) Pre-existing blind Jacobian ratios vs protected historical ratio: population statistics, not nearest-value fishing.

ratios=[]
dyn=OUT/'A057_DYNAMIC_RESULTS.jsonl'
if dyn.is_file():
    for line in dyn.read_text(encoding='utf-8').splitlines():
        x=json.loads(line)
        if isinstance(x.get('ratio21'),(int,float)) and x['ratio21']>0: ratios.append(float(x['ratio21']))
if ratios:
    target=float(reveal['historical_targets']['suppression_ratio']); dist=[abs(math.log(x/target)) for x in ratios]
    res['spectral_target']={'target':target,'n_blind_ratios':len(ratios),'median_blind_ratio':statistics.median(ratios),'median_abs_log_distance':statistics.median(dist),'fraction_within_5pct':sum(abs(x/target-1)<=.05 for x in ratios)/len(ratios),'fraction_within_10pct':sum(abs(x/target-1)<=.10 for x in ratios)/len(ratios),'fraction_within_20pct':sum(abs(x/target-1)<=.20 for x in ratios)/len(ratios)}
else: res['spectral_target']={'status':'NO_FROZEN_RATIO_POPULATION'}

# 6) Old component-count coherence factor vs measured total/self ratio for frozen multicomponent cases.
car=OUT/'A057_CARRIER_RESULTS.jsonl'; coh=[]
if car.is_file():
    nominal_by={}
    for line in car.read_text(encoding='utf-8').splitlines():
        x=json.loads(line); k=(x.get('topology_id'),x.get('carrier_id'))
        # select highest resolution and core scale closest to 1 without consulting targets
        old=nominal_by.get(k)
        score=(x.get('resolution',0),-abs(float(x.get('core_scale',1))-1.0))
        if old is None or score>(old[0],old[1]): nominal_by[k]=(score[0],score[1],x)
    target_base=float(reveal['historical_targets']['suppression_ratio'])
    for _,_,x in nominal_by.values():
        n=int(x.get('geometry',{}).get('component_count',1));selfe=x.get('decomposition',{}).get('self');tot=x.get('decomposition',{}).get('total')
        if n>1 and isinstance(selfe,(int,float)) and isinstance(tot,(int,float)) and selfe!=0 and tot/selfe>0:
            measured=tot/selfe; historical=n**(-1.0/target_base);coh.append({'topology_id':x['topology_id'],'component_count':n,'measured_total_over_self':measured,'historical_component_factor':historical,'abs_log_distance':abs(math.log(measured/historical))})
if coh:
    res['coherence_target']={'rows':coh,'median_abs_log_distance':statistics.median([x['abs_log_distance'] for x in coh])}
else: res['coherence_target']={'status':'NO_POSITIVE_MULTICOMPONENT_COHERENCE_CASES'}

# 7) Explicitly distinguish models that were structural organizers from numerically closed models.
res['closure_status']={
 'direct_regularized_line_energy':'NUMERICALLY_EVALUATED_BLIND',
 'core_tube_energy':'NUMERICALLY_EVALUATED_BLIND_DIAGNOSTIC',
 'historical_factorized_composite':'NUMERICALLY_EVALUATED_AFTER_COMMITMENT_REVEAL',
 'universal_topological_kernel':'NOT_NUMERICALLY_CLOSED_WITHOUT_AN_INDEPENDENT_KERNEL_DEFINITION',
 'rosetta_factorized_kernel':'PARTIALLY_EVALUABLE; CLOCK_FACTOR_AND_GEOMETRIC_EXPOSURE_CAN_BE_TESTED, BUT THE_TOPOLOGICAL_KERNEL_REQUIRES_INDEPENDENT_COEFFICIENT_CLOSURE',
 'thread_suppression':'NOT_EVALUABLE_FROM_CENTERLINE_ONLY_PKLSA_WITHOUT_AN_EXPLICIT_MULTI_THREAD_STATE'
}

post=ROOT.parent/'A057-v0.1.1-post_reveal_analysis';post.mkdir(exist_ok=True)
write_json(post/'POST_REVEAL_COMPARISON.json',res)
print(post/'POST_REVEAL_COMPARISON.json')
