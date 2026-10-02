\
from __future__ import annotations
import hashlib, json


def _resolved(seed: dict, metric: str) -> bool:
    return str((seed.get('observable_status') or {}).get(metric,'')).upper()=='RESOLVED'


def capability_flags(seed: dict, policy: dict) -> dict:
    out={}
    for name,metrics in policy['capabilities'].items():
        out[name]=all(_resolved(seed,m) for m in metrics)
    g3=str((seed.get('literature_gate_status') or {}).get('G3_signed_frenet_chirality_completeness','')).upper()
    out['chirality_ready']=out.get('chirality_ready',False) and g3=='PASS'
    return out


def static_ready(seed: dict, policy: dict) -> tuple[bool,list[str]]:
    p=policy['static_ready']; reasons=[]
    if p.get('require_literature_hard_gate_pass') and seed.get('literature_hard_gate_pass') is not True:
        reasons.append('literature_hard_gate_pass!=true')
    cls=str(seed.get('analysis_evidence_class') or '')
    if cls in set(p.get('exclude_evidence_classes',[])):
        reasons.append(f'evidence_class={cls}')
    for metric in p['required_core_observables']:
        if not _resolved(seed,metric): reasons.append(f'{metric}:not_RESOLVED')
    return not reasons,reasons


def seed_role(seed: dict, policy: dict) -> str:
    cls=str(seed.get('analysis_evidence_class') or '')
    p=policy['static_ready']
    if cls in p.get('primary_evidence_classes',[]): return 'PRIMARY_REFERENCE'
    if cls in p.get('secondary_evidence_classes',[]): return 'SECONDARY_QUALIFIED'
    if cls in p.get('control_evidence_classes',[]): return 'CONTROL_GENERATED'
    if cls=='MIRROR': return 'MIRROR_PROVENANCE_ONLY'
    return 'UNCLASSIFIED'


def source_locator(source_record: dict|None) -> dict:
    if not source_record: return {'status':'SOURCE_METADATA_UNAVAILABLE'}
    c=source_record.get('carrier',source_record)
    return {
      'status':'RESOLVABLE_FROM_WORKBENCH_SOURCE_METADATA',
      'source_path':c.get('source_path'),'reference_id':c.get('reference_id'),
      'representation':c.get('representation'),'raw_sha256':c.get('raw_sha256'),
      'geometry_sha256':source_record.get('geometry_sha256'),
      'catalog_id':c.get('catalog_id'),'source_family':c.get('source_family'),
      'source_role':c.get('source_role'),'variant_id':c.get('variant_id'),
      'relaxation_stage':(c.get('metadata') or {}).get('relaxation_stage'),
    }


def build_seed_record(seed: dict, source_record: dict|None, policy: dict) -> dict:
    ready,reasons=static_ready(seed,policy); caps=capability_flags(seed,policy); role=seed_role(seed,policy)
    loc=source_locator(source_record)
    payload={
      'topology_id':seed.get('topology_id'),'carrier_id':seed.get('carrier_id'),
      'static_ready':ready,'static_ready_reasons':reasons,'seed_role':role,
      'provider_group':seed.get('provider_group'),'lineage_group':seed.get('lineage_group'),
      'method_group':seed.get('method_group'),'source_family':seed.get('source_family'),
      'evidence_class':seed.get('analysis_evidence_class'),'capabilities':caps,
      'observable_status':seed.get('observable_status',{}),'finest_metrics':seed.get('finest_metrics',{}),
      'literature_gate_status':seed.get('literature_gate_status',{}),
      'finest_resolution':seed.get('finest_resolution'),'source_locator':loc,
      'scientific_boundary':'STATIC_READY is a geometry/numerics/provenance capability, not DYNAMICS_READY and not an SST particle claim.'
    }
    ident=json.dumps({'topology_id':payload['topology_id'],'carrier_id':payload['carrier_id'],'geometry_sha256':loc.get('geometry_sha256'),'policy_version':policy.get('policy_version')},sort_keys=True).encode()
    payload['static_seed_id']='SEED_'+hashlib.sha256(ident).hexdigest()[:16]
    return payload


def classify_seedsets(representatives: list[dict], source_records: dict[str,dict], policy: dict):
    records=[]
    for rep in representatives:
        records.append(build_seed_record(rep,source_records.get(str(rep.get('carrier_id'))),policy))
    primary=[r for r in records if r['static_ready'] and r['seed_role']=='PRIMARY_REFERENCE']
    secondary=[r for r in records if r['static_ready'] and r['seed_role']=='SECONDARY_QUALIFIED']
    controls=[r for r in records if r['static_ready'] and r['seed_role']=='CONTROL_GENERATED']
    rejected=[r for r in records if not r['static_ready']]
    return {'all':records,'primary':primary,'secondary':secondary,'controls':controls,'rejected':rejected}


ROLE_PRIORITY={
  "independent_ideal_reference_geometry":0,"ideal_reference_geometry":0,
  "relaxed_reference_geometry":1,"independent_reference_geometry":2,
  "reference_fourier_geometry":3,"derived_relaxed_geometry":4,
  "historical_relaxation_state":5,"generated_experimental_family":6,
}
STAGE_PRIORITY={"FINAL":0,"NEAR_IDEAL":1,"CONTINUED":2,"RELAXED_INTERMEDIATE":3,"N1200":4,"N0600":5,"SEED":6,"UNSPECIFIED":7}

def anchor_score(seed: dict):
    loc=seed.get("source_locator") or {}
    role=loc.get("source_role")
    stage=loc.get("relaxation_stage")
    role_rank=ROLE_PRIORITY.get(str(role),3 if "reference" in str(role).lower() else 8)
    stage_rank=STAGE_PRIORITY.get(str(stage),0 if "ideal" in str(role).lower() else 8)
    cap_count=sum(1 for v in (seed.get("capabilities") or {}).values() if v is True)
    res=int(seed.get("finest_resolution") or 0)
    return (role_rank,stage_rank,-cap_count,-res,str(seed.get("carrier_id")))

def provider_anchors(primary_seeds: list[dict]) -> list[dict]:
    from collections import defaultdict
    groups=defaultdict(list)
    for s in primary_seeds:
        if s.get("provider_group"): groups[str(s["provider_group"])].append(s)
    out=[]
    for provider,seeds in sorted(groups.items()):
        chosen=dict(sorted(seeds,key=anchor_score)[0])
        chosen["provider_anchor"]=True
        chosen["provider_anchor_policy"]="provenance/stage priority -> capability completeness -> resolution -> stable carrier_id; no SST observable value is optimized"
        chosen["provider_candidate_count"]=len(seeds)
        out.append(chosen)
    return out
