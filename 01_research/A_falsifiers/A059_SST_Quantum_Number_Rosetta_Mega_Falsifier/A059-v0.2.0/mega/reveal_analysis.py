from __future__ import annotations
from pathlib import Path
import csv, json, sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from framework_bootstrap import load_framework
FRAMEWORK=load_framework()
from sst_falsifier.blind import verify_reveal, verify_blind_terms
from sst_falsifier.outputs import make_output_manifest, deterministic_zip
from .common import *


def rows_csv(path: Path):
    if not path.is_file(): return []
    with path.open(encoding='utf-8-sig') as f: return list(csv.DictReader(f))


def main():
    out=output_root(ROOT); revdir=out/'revealed'
    if not (out/'RUN_SUMMARY_REVEALED.json').is_file() or not (revdir/'reveal.json').is_file():
        raise SystemExit('Canonical reveal artifacts are missing. Run run_all.cmd REVEAL after BLIND.')
    policy=read_json(ROOT/'blind_policy.json'); nonce=ROOT/policy['private_nonce_path']
    ok1,_=verify_reveal(ROOT/policy['private_reveal_path'],nonce,ROOT/policy['reveal_commitment_path'])
    ok2,_=verify_blind_terms(ROOT/policy['private_forbidden_terms_path'],nonce,ROOT/policy['commitment_path'])
    if not(ok1 and ok2): raise RuntimeError('reveal commitment verification failed')
    reveal=read_json(ROOT/'private'/'reveal.json')
    reverse={opaque_topology(x['topology_id'],ROOT):x['topology_id'] for x in atlas_csv('STATIC_READY_INDEX.csv',ROOT)}

    family=read_json(phase_dir('P02',ROOT)/'FAMILY_DYNAMIC_CLASSIFICATION.json') if (phase_dir('P02',ROOT)/'FAMILY_DYNAMIC_CLASSIFICATION.json').is_file() else {}
    fam_pred=[]
    for x in family.get('predictions',[]):
        y=dict(x); y['topology_id']=reverse.get(x.get('candidate_id')); fam_pred.append(y)

    charge_rows=rows_csv(phase_dir('P03',ROOT)/'DYNAMIC_CHARGE_PAIR_RANKING.csv')
    revealed_pairs=[]
    for x in charge_rows:
        y=dict(x); y['topology_A']=reverse.get(x.get('candidate_A')); y['topology_B']=reverse.get(x.get('candidate_B')); revealed_pairs.append(y)
    target=set(reveal['semantic_hypotheses']['period_charge']['committed_first_pair_to_inspect'])
    target_hits=[x for x in revealed_pairs if {x.get('topology_A'),x.get('topology_B')}==target]

    container=load_phase_result('P06',ROOT)
    score={
      'schema':'A059-REVEALED-ROSETTA-SCORECARD-2',
      'commitments_verified':True,
      'semantic_hypotheses':reveal['semantic_hypotheses'],
      'family_dynamic_predictions_revealed':fam_pred,
      'committed_first_pair_dynamic_charge_rows':target_hits,
      'container_phase':None if container is None else {'status':container.get('status'),'evidence_class':container.get('evidence_class'),'metrics':container.get('metrics')},
      'blind_results_unchanged':True,
      'guards':reveal.get('reveal_guards',[]),
    }
    score_path=revdir/'A059_REVEALED_ROSETTA_SCORECARD.json'; write_json(score_path,score)
    make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    z=ROOT.parent/'A059_SST_Quantum_Number_Rosetta_Mega_Falsifier_v0.2.0-outputs_REVEALED.zip'
    deterministic_zip(out,z,exclude_parts={'__pycache__','.pytest_cache','.venv','build'})
    print(json.dumps({'scorecard':str(score_path),'revealed_zip':str(z),'target_pair_rows':len(target_hits)},indent=2))
    return 0

if __name__=='__main__': raise SystemExit(main())
