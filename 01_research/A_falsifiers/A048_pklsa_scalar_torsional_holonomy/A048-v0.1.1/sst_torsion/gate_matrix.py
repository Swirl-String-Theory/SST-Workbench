"""Full backlog classification from this run, never from historical labels."""
import json
from pathlib import Path


def from_evidence(run, report):
    run=Path(run)
    template=Path(__file__).resolve().parents[1]/'GATE_STATUS_MATRIX.json'
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
    result['counts']={s:sum(x['status']==s for x in result['items']) for s in result['allowed_statuses']}
    return result
