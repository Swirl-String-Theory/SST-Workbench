"""A065 v0.3.3 preregistered fail-closed numerical readiness and provenance guards.

This is *not* a physical validation gate and must never yield G3 PASS.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path

SPEC_NAME = 'ROUTING_V033.json'


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evaluate(root, reference_gates, q, *, g10_status):
    root=Path(root)
    spec=json.loads((root/'preregistration'/SPEC_NAME).read_text(encoding='utf-8'))
    # Verify the instance's pre-freeze science contract (or portable audit) pinned
    # these exact routing bytes; modifying preregistration after freeze is invalid.
    reg_digest=_sha(root/'preregistration'/SPEC_NAME)
    science=root/'science_contract.json'
    if science.is_file():
        assumptions=json.loads(science.read_text(encoding='utf-8')).get('assumptions',[])
        pinned=any('v0.3.3 preregistered routing SHA256='+reg_digest in a for a in assumptions)
    else:
        aud=root/'docs/RELEASE_V033_AUDIT.json'
        pinned=aud.is_file() and json.loads(aud.read_text(encoding='utf-8')).get('v033_routing_prereg_sha256')==reg_digest
    if not pinned:
        raise ValueError('V033_UNPINNED_OR_MODIFIED_ROUTING_PREREGISTRATION')
    expected=set(spec['exact_legacy_failure_ids'])
    actual={g['gate'] for g in reference_gates if g['status']!='PASS'}
    if spec['schema']!='A065-ROUTING-V033-PREREG-1' or spec['release']!='v0.3.3':
        raise ValueError('INVALID_V033_PREREGISTRATION_SCHEMA')
    if spec['gate_change']['G3_requires']!=['G1','G10']:
        raise ValueError('V033_GATE_DEPENDENCY_TAMPERING')
    if spec['qualified_run_G3_status']!='UNRESOLVED' or not all(spec[k] for k in ('no_target_fit','no_reveal','no_new_physics')):
        raise ValueError('V033_SCOPE_TAMPERING')
    # Disallow substitute source geometry, modified seals and posthoc tolerance changes.
    source_mismatches=[rel for rel, sha in spec['protected_v032_file_sha256'].items() if
                       not (root/rel).is_file() or _sha(root/rel)!=sha]
    qualified=q['qualification']
    status_matches=(
        q['precommit_sha256']==spec['original_v032_qualification_prereg_sha256']
        and qualified['historical_fail_retained']=='FAIL'
        and qualified['refined_discretization']=='PASS'
        and qualified['time_discretization']=='PASS'
        and g10_status=='PASS'
    )
    # Exact legacy footprint: no other gate is whitelisted. Any new failure blocks evaluation.
    ready=(not source_mismatches
           and len(reference_gates)==spec['expected_reference_gate_count']
           and actual==expected and status_matches)
    return {
        'schema':'A065-ROUTING-DECISION-V033-1','release':'v0.3.3',
        'ready_for_G3_evaluation':ready,
        'prereg_sha256':_sha(root/'preregistration'/SPEC_NAME),
        'historical_G2':'FAIL_RETAINED',
        'observed_failure_ids':sorted(actual),'expected_failure_ids':sorted(expected),
        'reference_count':len(reference_gates),
        'protected_mismatches':source_mismatches,
        'g10_status':g10_status,
        'time_discretization':qualified['time_discretization'],
        'g3_permitted_outcome':'UNRESOLVED' if ready else 'NOT_RUN_PREREQUISITE',
        'physical_force_status':'UNRESOLVED',
        'scope':'Execution-eligibility diagnostics only. NOT Casimir, gravity, full Euler or PKLSA physical validation.'
    }
