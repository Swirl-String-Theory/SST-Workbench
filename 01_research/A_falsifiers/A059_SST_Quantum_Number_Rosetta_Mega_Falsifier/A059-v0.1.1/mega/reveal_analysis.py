from __future__ import annotations
from pathlib import Path
import csv,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from framework_bootstrap import load_framework
FRAMEWORK=load_framework()
from sst_falsifier.blind import verify_reveal,verify_blind_terms
from sst_falsifier.outputs import make_output_manifest,deterministic_zip
from .common import *


def rows_csv(path):
    if not path.is_file():return []
    with path.open(encoding='utf-8-sig') as f:return list(csv.DictReader(f))

def main():
    out=output_root(ROOT);revdir=out/'revealed'
    if not (out/'RUN_SUMMARY_REVEALED.json').is_file() or not (revdir/'reveal.json').is_file():
        raise SystemExit('Run run_11_reveal_if_allowed.cmd first; canonical framework reveal artifacts are missing.')
    policy=read_json(ROOT/'blind_policy.json');nonce=ROOT/policy['private_nonce_path']
    ok1,d1=verify_reveal(ROOT/policy['private_reveal_path'],nonce,ROOT/policy['reveal_commitment_path'])
    ok2,d2=verify_blind_terms(ROOT/policy['private_forbidden_terms_path'],nonce,ROOT/policy['commitment_path'])
    if not(ok1 and ok2):raise RuntimeError('reveal commitment verification failed')
    reveal=read_json(ROOT/'private'/'reveal.json')
    # Create reverse opaque map for all E011 objects.
    idx=atlas_csv('STATIC_READY_INDEX.csv',ROOT);rev={opaque_topology(x['topology_id'],ROOT):x['topology_id'] for x in idx}
    # Reveal P03 rankings and locate committed family-B first-pair hypothesis without changing its blind score/rank.
    ranks=rows_csv(phase_dir('P03',ROOT)/'PAIR_DISCOVERY_RANKING.csv')
    revealed_ranks=[]
    for x in ranks:
        y=dict(x);y['topology_A']=rev.get(x['candidate_A']);y['topology_B']=rev.get(x['candidate_B']);revealed_ranks.append(y)
    target_pair=set(reveal['semantic_hypotheses']['family_B']['generation_pair_hypothesis'][0])
    target_hits=[x for x in revealed_ranks if {x.get('topology_A'),x.get('topology_B')}==target_pair]
    # Reveal P01 cluster assignments.
    feats=rows_csv(phase_dir('P01',ROOT)/'ANONYMOUS_FEATURE_SPACE.csv')
    revealed_features=[]
    for x in feats:
        y=dict(x);y['topology_id']=rev.get(x['candidate_id']);revealed_features.append(y)
    semantic={}
    for key,h in reveal['semantic_hypotheses'].items():
        if isinstance(h,dict) and h.get('e011_members'):
            members=set(h['e011_members']);sub=[x for x in revealed_features if x.get('topology_id') in members]
            semantic[key]={'semantic_role':h.get('semantic_role'),'members':h['e011_members'],'cluster_assignments':[{'topology_id':x.get('topology_id'),'cluster':x.get('cluster')} for x in sub]}
    score={'schema':'A056-REVEALED-ROSETTA-SCORECARD-1','commitments_verified':True,'semantic_hypotheses':reveal['semantic_hypotheses'],'family_cluster_readout':semantic,'committed_first_pair_signed_response_hits':target_hits,'blind_results_unchanged':True,'guards':reveal.get('reveal_guards',[])}
    score_path=revdir/'A056_REVEALED_ROSETTA_SCORECARD.json'
    write_json(score_path,score)
    _=make_output_manifest(out,out/'OUTPUT_MANIFEST.json')
    cfg_name='A056_SST_Quantum_Number_Rosetta_Mega_Falsifier_v0.1.1-outputs_REVEALED.zip'
    z=ROOT.parent/cfg_name
    deterministic_zip(out,z,exclude_parts={'__pycache__','.pytest_cache','.venv','build'})
    print(json.dumps({'scorecard':str(score_path),'revealed_zip':str(z),'target_pair_rows':len(target_hits)},indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
