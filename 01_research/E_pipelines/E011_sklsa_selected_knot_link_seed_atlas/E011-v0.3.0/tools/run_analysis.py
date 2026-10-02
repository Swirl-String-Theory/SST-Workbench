\
from __future__ import annotations
import argparse, json, sys, tempfile, hashlib
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from sklsa.selection import load_selection, selected_ids
from sklsa.parent import normalize_workbench_root, locate_e010_output, validate_e010_release, extract_e010_subset
from sklsa.loaders import load_topology_bundle, load_source_records
from sklsa.analysis import admission_record, join_carriers, build_availability, representative_rows, mirror_fallback_representative, consensus_rows, pairwise_rows, summarize_topology
from sklsa.static_ready import build_seed_record, provider_anchors
from sklsa.agreement import provider_agreement_rows, topology_agreement_status
from sklsa.output import write_json, write_jsonl, write_csv


def file_sha256(path: Path):
    h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()


def main()->int:
    ap=argparse.ArgumentParser(description='E011 SKLSA v0.3.0 — provider agreement, uncertainty and STATIC_READY seedsets')
    ap.add_argument('--workbench-root',default=r'C:\workspace\projects\SST-Workbench')
    ap.add_argument('--e010-output',help='E010-v0.3.1 output directory or ZIP')
    ap.add_argument('--mode',choices=['poc','core','selected'],default='selected')
    ap.add_argument('--include-sentinels',action='store_true'); ap.add_argument('--include-controls',action='store_true')
    ap.add_argument('--output-root'); args=ap.parse_args()

    root=Path(args.workbench_root).absolute() if args.e010_output else normalize_workbench_root(args.workbench_root)
    selection=load_selection(HERE/'configs'/'selected_topologies.json')
    parent_contract=json.loads((HERE/'configs'/'parent_e010.json').read_text(encoding='utf-8'))
    metric_cfg=json.loads((HERE/'configs'/'metrics.json').read_text(encoding='utf-8'))
    policy=json.loads((HERE/'configs'/'static_ready_policy.json').read_text(encoding='utf-8'))
    if args.mode=='poc': wanted=list(selection['poc'])
    elif args.mode=='core': wanted=list(selection['core_knots'])
    else: wanted=selected_ids(selection,include_controls=args.include_controls,include_sentinels=args.include_sentinels)
    wanted=list(dict.fromkeys(wanted))

    located=locate_e010_output(root,args.e010_output); tmp=None
    parent_input={'input_kind':'directory','input_path':str(located)}
    if located.is_file():
        tmp=tempfile.TemporaryDirectory(prefix='e011_v030_e010_subset_')
        e010,meta=extract_e010_subset(located,wanted,Path(tmp.name)); parent_input.update(meta)
    else: e010=located
    chk=validate_e010_release(e010,parent_contract); release=chk['release']; parent_warnings=chk['warnings']
    campaign=json.loads((e010/'CAMPAIGN_INDEX.json').read_text(encoding='utf-8')); campaign_passed=set(campaign.get('passed',[]))

    out=Path(args.output_root) if args.output_root else HERE/'E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs'
    out.mkdir(parents=True,exist_ok=True)
    family_order=metric_cfg['source_family_order']; metric_names=metric_cfg['metrics']
    all_carriers=[]; all_admitted=[]; all_availability=[]; all_reps=[]; all_consensus=[]; all_pairs=[]
    all_seed_records=[]; all_primary=[]; all_secondary=[]; all_controls=[]; all_rejected=[]; all_agreement=[]; all_anchors=[]
    topology_summaries=[]; admission_rows=[]; static_index=[]; operational_errors=[]

    for topology_id in wanted:
        bundle=load_topology_bundle(e010,topology_id); admission=admission_record(bundle,campaign_passed); admission_rows.append(admission)
        topo_dir=out/'topologies'/topology_id
        if bundle.get('status')!='LOADED':
            operational_errors.append({'topology_id':topology_id,'error':bundle.get('status'),'missing':bundle.get('missing',[])})
            row={'topology_id':topology_id,'static_ready':False,'static_status':'ERROR_MISSING_E010_ARTIFACTS','primary_seed_count':0}
            static_index.append(row); write_json(topo_dir/'STATIC_READY.json',row); continue
        carriers=join_carriers(bundle)
        for r in carriers: r['topology_id']=topology_id
        availability=build_availability(bundle,family_order,carriers); admitted=[c for c in carriers if c.get('literature_hard_gate_pass') is True]
        strict=[]; extended=[]; mirror=[]; consensus=[]; pairs=[]
        if admission.get('admitted'):
            strict=representative_rows(admitted,'strict_upstream'); extended=representative_rows(admitted,'extended_qualified')
            if not extended: mirror=mirror_fallback_representative(admitted)
            for r in strict+extended+mirror: r['topology_id']=topology_id
            consensus=consensus_rows(topology_id,strict,metric_names,'strict_upstream')+consensus_rows(topology_id,extended,metric_names,'extended_qualified')
            pairs=pairwise_rows(topology_id,strict,metric_names,'strict_upstream')+pairwise_rows(topology_id,extended,metric_names,'extended_qualified')
        source_records=load_source_records(e010,topology_id)
        seed_records=[]
        for carrier in admitted:
            seed_records.append(build_seed_record(carrier,source_records.get(str(carrier.get('carrier_id'))),policy))
        # Every admissible non-mirror carrier remains in the seedset; provider agreement uses
        # provider medians, so a provider with many historical variants never receives extra votes.
        primary=[r for r in seed_records if r['static_ready'] and r['seed_role']=='PRIMARY_REFERENCE']
        secondary=[r for r in seed_records if r['static_ready'] and r['seed_role']=='SECONDARY_QUALIFIED']
        controls=[r for r in seed_records if r['static_ready'] and r['seed_role']=='CONTROL_GENERATED']
        rejected=[r for r in seed_records if not r['static_ready']]
        anchors=provider_anchors(primary)
        seedsets={'all':seed_records,'primary':primary,'secondary':secondary,'controls':controls,'rejected':rejected,'anchors':anchors}
        agreement=provider_agreement_rows(topology_id,primary,policy)
        agreement_status,reasons=topology_agreement_status(primary,agreement,policy)
        static_ready_topology=bool(primary)
        static_not_ready_reasons=[]
        if static_ready_topology:
            static_status=agreement_status
        elif not admission.get('admitted'):
            static_status='STATIC_NOT_READY_E010_EXCLUDED'
            static_not_ready_reasons=[str(admission.get('admission_status'))]
        elif any(c.get('analysis_evidence_class')=='UPSTREAM_INDEPENDENT' for c in admitted):
            static_status='STATIC_NOT_READY_CORE_OBSERVABLES'
            for r in rejected:
                if r.get('seed_role')=='PRIMARY_REFERENCE':
                    static_not_ready_reasons.extend(r.get('static_ready_reasons',[]))
            static_not_ready_reasons=sorted(set(static_not_ready_reasons))
        elif any(c.get('analysis_evidence_class')=='MIRROR' for c in admitted):
            static_status='STATIC_NOT_READY_MIRROR_ONLY'
            static_not_ready_reasons=['no_independent_upstream_primary_seed','mirror_never_static_ready']
        else:
            static_status='STATIC_NOT_READY_NO_UPSTREAM_REFERENCE'
            static_not_ready_reasons=['no_independent_upstream_primary_seed']
        row={
          'topology_id':topology_id,'e010_carrier_admitted':bool(admission.get('admitted')),
          'static_ready':static_ready_topology,'static_status':static_status,
          'provider_agreement_reasons':reasons,'static_not_ready_reasons':static_not_ready_reasons,'primary_seed_count':len(primary),
          'primary_provider_count':len({s.get('provider_group') for s in primary if s.get('provider_group')}),
          'provider_anchor_count':len(anchors),
          'secondary_seed_count':len(secondary),'control_seed_count':len(controls),
          'rejected_carrier_count':len(rejected),
          'primary_static_seed_ids':[s['static_seed_id'] for s in primary],
          'primary_carrier_ids':[s['carrier_id'] for s in primary],
          'provider_anchor_seed_ids':[s['static_seed_id'] for s in anchors],
        }
        static_index.append(row)
        topo_summary=summarize_topology(bundle,admission,carriers,strict,extended,mirror)
        topo_summary.update(row); topology_summaries.append(topo_summary)

        write_json(topo_dir/'E010_ADMISSION.json',admission); write_json(topo_dir/'CARRIER_AVAILABILITY.json',availability)
        write_json(topo_dir/'E010_CARRIERS.json',carriers); write_json(topo_dir/'ADMITTED_CARRIERS.json',admitted)
        write_json(topo_dir/'PROVIDER_REPRESENTATIVES.json',{'strict_upstream':strict,'extended_qualified':extended,'mirror_fallback_provenance_only':mirror})
        write_json(topo_dir/'PROVIDER_AGREEMENT.json',agreement); write_json(topo_dir/'STATIC_READY_SEEDSET.json',{'summary':row,'provider_anchors':anchors,'primary':primary,'secondary':secondary,'controls':controls,'rejected':rejected})
        write_json(topo_dir/'SUMMARY.json',topo_summary)

        all_carriers+=carriers; all_admitted+=admitted; all_availability+=availability; all_reps+=strict+extended+mirror
        all_consensus+=consensus; all_pairs+=pairs; all_agreement+=agreement; all_seed_records+=seed_records; all_primary+=primary; all_secondary+=secondary; all_controls+=controls; all_rejected+=rejected; all_anchors+=anchors

    write_json(out/'PARENT_RELEASE.json',release); write_json(out/'PARENT_INPUT.json',parent_input); write_json(out/'PARENT_WARNINGS.json',parent_warnings)
    write_json(out/'SELECTION.json',{'mode':args.mode,'topology_ids':wanted,'include_sentinels':args.include_sentinels,'include_controls':args.include_controls})
    write_json(out/'STATIC_READY_POLICY.json',policy); write_json(out/'STATIC_READY_INDEX.json',static_index); write_csv(out/'STATIC_READY_INDEX.csv',static_index)
    write_json(out/'E010_ADMISSION_MATRIX.json',admission_rows); write_csv(out/'E010_ADMISSION_MATRIX.csv',admission_rows)
    write_json(out/'TOPOLOGY_SUMMARIES.json',topology_summaries); write_json(out/'OPERATIONAL_ERRORS.json',operational_errors)
    write_jsonl(out/'E010_CARRIERS.jsonl',all_carriers); write_jsonl(out/'ADMITTED_CARRIERS.jsonl',all_admitted); write_jsonl(out/'PROVIDER_REPRESENTATIVES.jsonl',all_reps)
    write_csv(out/'CARRIER_AVAILABILITY.csv',all_availability); write_csv(out/'METRIC_CONSENSUS.csv',all_consensus); write_csv(out/'PAIRWISE_METRIC_DELTAS.csv',all_pairs)
    write_json(out/'PROVIDER_AGREEMENT.json',all_agreement); write_csv(out/'PROVIDER_AGREEMENT.csv',all_agreement); write_csv(out/'UNCERTAINTY_ENVELOPES.csv',all_agreement)
    write_jsonl(out/'STATIC_READY_SEEDS.jsonl',all_seed_records); write_jsonl(out/'STATIC_READY_PROVIDER_ANCHORS.jsonl',all_anchors); write_jsonl(out/'STATIC_READY_PRIMARY_SEEDS.jsonl',all_primary); write_jsonl(out/'STATIC_READY_SECONDARY_SEEDS.jsonl',all_secondary); write_jsonl(out/'STATIC_READY_CONTROL_SEEDS.jsonl',all_controls)
    write_json(out/'STATIC_READY_SEEDSETS.json',{'schema':'E011-STATIC-READY-SEEDSETS-1','policy_version':policy['policy_version'],'provider_anchors':all_anchors,'primary':all_primary,'secondary':all_secondary,'controls':all_controls,'rejected_representatives':all_rejected})
    contract={
      'schema':'E011-STATIC-SEED-CONTRACT-1','atlas_version':'0.3.0',
      'consumer_rule':'Falsifiers select by topology_id + required capability flags + minimum evidence tier. They must not hard-code an arbitrary source file when a STATIC_READY manifest entry exists.',
      'minimum_fields':['static_seed_id','topology_id','carrier_id','seed_role','provider_group','source_locator.geometry_sha256','capabilities'],
      'evidence_tiers':['CROSS_PROVIDER_ROBUST','CROSS_PROVIDER_SENSITIVE','CROSS_PROVIDER_INCOMPLETE','SINGLE_PROVIDER_QUALIFIED'],
      'example_request':{'topology_id':'3_1','require_static_ready':True,'required_capabilities':['writhe_ready','acn_ready'],'minimum_independent_providers':2},
      'dynamics_ready':False,
    }
    write_json(out/'SEED_CONTRACT_SCHEMA.json',contract)

    execution='PASS' if not operational_errors and len(static_index)==len(wanted) else 'FAIL_CLOSED'
    counts=Counter(r['static_status'] for r in static_index)
    ready=[r for r in static_index if r['static_ready']]
    summary={
      'schema':'E011-SKLSA-STATIC-READY-ATLAS-1','e011_version':'0.3.0','created_utc':datetime.now(timezone.utc).isoformat(),
      'workbench_root':str(root),'e010_input_kind':parent_input.get('input_kind'),'e010_input':parent_input.get('input_path'),'e010_input_sha256':parent_input.get('input_sha256'),'e010_release_version':release.get('e010_version'),
      'selected_topology_count':len(wanted),'e010_carrier_admitted_topology_count':sum(1 for r in admission_rows if r.get('admitted')),
      'static_ready_topology_count':len(ready),'static_not_ready_topology_count':len(wanted)-len(ready),'static_status_counts':dict(counts),
      'primary_static_seed_count':len(all_primary),'provider_anchor_count':len(all_anchors),'secondary_static_seed_count':len(all_secondary),'control_static_seed_count':len(all_controls),
      'provider_agreement_topology_count':sum(1 for r in static_index if int(r.get('primary_provider_count',0))>=2),
      'cross_provider_robust_topology_count':counts.get('CROSS_PROVIDER_ROBUST',0),'cross_provider_sensitive_topology_count':counts.get('CROSS_PROVIDER_SENSITIVE',0),'cross_provider_incomplete_topology_count':counts.get('CROSS_PROVIDER_INCOMPLETE',0),'single_provider_qualified_topology_count':counts.get('SINGLE_PROVIDER_QUALIFIED',0),
      'operational_error_count':len(operational_errors),'execution_gate':execution,
      'static_ready_definition':'At least one independent upstream carrier passes E010 hard literature gates and has RESOLVED Wr, ACN, dcsd and kappa_rms. Additional observables are expressed as capability flags rather than silently required.',
      'provider_agreement_definition':'Empirical uncertainty across independent upstream STATIC_READY seeds grouped by provider. Each provider contributes one median per observable; within-provider spread is retained. No composite best-seed score is used.',
      'scientific_boundary':'STATIC_READY supports static geometry SST falsifiers. It does not establish finite-core/Biot-Savart/Kelvin/Floquet DYNAMICS_READY, dynamical stability, particle identity, or any SST physical claim.'
    }
    write_json(out/'RUN_SUMMARY.json',summary); print(json.dumps(summary,indent=2))
    if tmp: tmp.cleanup()
    return 0 if execution=='PASS' else 2

if __name__=='__main__': raise SystemExit(main())
