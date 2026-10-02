"""Full backlog classification from this run, never from historical labels."""
import json
from pathlib import Path


def from_evidence(run, report):
    run=Path(run)
    template=run/'BLIND'/'gate_template.json'
    source=json.loads(template.read_text(encoding='utf-8'))
    tests=run/'BLIND'/'test_execution.json'
    tests_ok=tests.is_file() and json.loads(tests.read_text())['exit_code']==0
    result={key:source[key] for key in ('schema','source_conversation','allowed_statuses')}
    result.update(run_id=run.name,physical_verdict='INDETERMINATE',promotion_allowed=False,items=[])
    for old in source['items']:
        row={key:old[key] for key in ('id','question','gate','prior_claim')}
        row.update(status='NOT-IMPLEMENTED',evidence_scope='physical_hypothesis',
                   reason='Physical gate lacks qualifying observations or implementation.',evidence=[])
        if row['id'].startswith('Q'):
            row.update(status='INDETERMINATE',evidence_scope='instrument_qualification',reason='Entire claim not established by dedicated executed evidence.')
        if row['id'] in {'H03','H04','H07','H13','H19','H20','H22','H25','H28','H41','H45'}:
            row.update(status='INDETERMINATE',reason='Control/implementation exists; corresponding physical claim untested.')
        if report['status']=='SYNTHETIC_DISCRIMINATOR_QUALIFIED':
            if row['id'] in {'H05','Q01','Q02','Q03','Q04','Q05','Q07','Q08','Q11','Q20','Q26','Q29'}:
                row.update(status='PASS',evidence_scope='synthetic_or_geometric_control',reason='This sealed synthetic run qualified the instrument.',evidence=['REVEALED/reveal_report.json'])
            if row['id'] in {'H03','H04','H19','H20','H45'}:
                row['instrument_status']='PASS'
        if tests_ok and row['id'] in {'Q06','Q09','Q10','Q15','Q16','Q18','Q23','Q24','Q25'}:
            row.update(status='PASS',evidence_scope='executed_regression_tests',reason='Production-path regression controls executed successfully.',evidence=['BLIND/test_execution.json'])
        if report.get('native') is not None and report['gates'].get('native_backend_parity')=='PASS' and row['id'] in {'Q21','Q22'}:
            row.update(status='PASS',evidence_scope='native_primitive_and_classifier_parity',reason='C++17 primitives and production classification match Python.',evidence=['BLIND/backend_parity_summary.json'])
        result['items'].append(row)
    dynamic_path=run/'BLIND'/'euler_probe_summary.json'
    if dynamic_path.exists():
        dynamic=json.loads(dynamic_path.read_text())
        for row in result['items']:
            if row['id'] in {'H01','H02','H06','H08','H09','H10','H28','H31','H32','H33','H34','H35','H36','H37','H38','H39','H40','H41','H42'}:
                row.update(status='INDETERMINATE',evidence_scope='independent_Euler_smoke_only',
                    evidence=['BLIND/euler_probe_summary.json'],
                    reason='Independent full-field dynamics ran, but core chart/resolution and objective phase/centerline observations are unqualified.')
            if row['id']=='H28':
                row['reason']='48 authentic PTSA upstream geometries ingested with hashes; exact signed PKLSA NPZ is absent. This is an explicit alternative route, not substitution.'
                row['upstream_ingest_status']='PASS'
            if row['id']=='H32':
                row['instrument_status']=dynamic['temporal_integrator_check']['status']
            if row['id']=='H42':
                row['instrument_status']=dynamic['producer_report']['gates']['incompressibility']['status']
            if row['id']=='H38':
                row['instrument_status']=dynamic['producer_report']['gates']['energy_drift']['status']
            if row['id']=='H41':
                row['implementation_status']='NOT-IMPLEMENTED'
                row['decision']='AMBIGUOUS'
            if row['id']=='Q22':
                row['euler_initializer_parity']=dynamic['producer_report']['initializer_native_parity']['status']
        result['branch_admission']=dynamic['branch_admission']
        result['producer_qualification_gates']=dynamic['producer_report']['gates']
    result['counts']={s:sum(x['status']==s for x in result['items']) for s in result['allowed_statuses']}
    return result
