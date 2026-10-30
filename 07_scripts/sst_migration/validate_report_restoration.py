"""Post-run report/ledger/archive checks, no scientific recomputation."""
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile

from pypdf import PdfReader

sys.dont_write_bytecode = True
from preflight import ROOT, read, sha
from restore_report_prepare import OUT, FAMILY
from phase3_prepare import snapshot, create_json


def normalize(value):
    return ''.join(c.lower() for c in value if c.isalnum())


def main():
    root = FAMILY/'A011-v0.4.1'
    sys.path.insert(0, str(root/'src'))
    from maxwell_sst_falsifier.framework_v110 import qualified_framework, verify_protocol
    qualified_framework(root)
    verify_protocol(root)
    from sst_falsifier.outputs import verify_output_manifest, verify_science_evidence_manifest
    from sst_falsifier.report import validate_report, write_auto_results_tex, write_auto_science_tex
    assert validate_report(root/'report/FALSIFIER_REPORT.tex') == []
    history = [json.loads(s) for s in (root/'PUBLICATIONS.jsonl').read_text().splitlines()]
    assert len(history) >= 2
    retained_count = len(history)
    required = ['Identification, version and authority', 'Research question and scientific objective', 'Null and alternative hypotheses',
                'Assumptions, domain and edge cases', 'Symbols, definitions, SI units', 'Registered equations and code-to-mathematics',
                'Algorithm, phases and execution order', 'Sources, provenance and dataset qualification', 'Numerical methods, tolerances and convergence',
                'Automatic results, tables and diagnostic graphs', 'Migration, execution and scientific gates', 'Backend manifest and authority',
                'Interpretation, falsification limits and unresolved claims', 'References and primary reproducibility records']
    reports = []
    for item in history[-2:]:
        canonical = root / (item['output_prefix']+'_v0.4.1_outputs')
        out = canonical if read(canonical/'RUN_ID.json')['run_id'] == item['run_id'] else root/(canonical.name+'__'+item['run_id'])
        manifest_ok, _ = verify_output_manifest(out, out/'OUTPUT_MANIFEST.json')
        evidence_ok, _ = verify_science_evidence_manifest(out, out/'SCIENCE_EVIDENCE_MANIFEST.json')
        assert manifest_ok and evidence_ok
        ledger = read(out/'GATE_LEDGER.json')
        data = read(out/'REPORT_DATA.json')
        assert data['gates'] == ledger['records']
        assert data['gate_axes']['scientific_gate'] == 'UNRESOLVED_MISSING_PHYSICAL_INPUTS'
        assert data['gate_axes']['scientific_status_promoted'] is False
        by_id = {r['gate_id']:r for r in ledger['records']}
        assert by_id['G5']['qualification'] == 'DIAGNOSTIC_ONLY'
        assert by_id['G5']['allows_dependent_claim'] is False
        assert all(by_id[k]['execution_status']=='NOT_EXECUTED' for k in ['G3','G4','G7','G8'])
        plot = read(out/'PLOT_DATA.json')
        for a, b in zip(plot, data['results']):
            assert a['length_native'] == [m['length_units'] for m in b['metrics_by_resolution']]
            assert a['writhe'] == [m['writhe_midpoint'] for m in b['metrics_by_resolution']]
        pdf = Path(item['report_pdf'])
        reader = PdfReader(pdf)
        text = '\n'.join(pg.extract_text() or '' for pg in reader.pages)
        clean = normalize(text)
        missing = [s for s in required if normalize(s) not in clean]
        assert not missing, missing
        for gate in ledger['records']:
            assert normalize(gate['status']) in clean and normalize(gate['qualification']) in clean
        with tempfile.TemporaryDirectory() as temp:
            auto = Path(temp)/'AUTO_RESULTS.tex'
            write_auto_results_tex(root, out, auto)
            assert auto.read_bytes() == (out/'report/AUTO_RESULTS.tex').read_bytes()
            write_auto_science_tex(root, auto)
            assert auto.read_bytes() == (out/'report/AUTO_SCIENCE_CONTRACT.tex').read_bytes()
        archive = Path(item['archive']['zip'])
        assert sha(archive) == item['archive']['sha256'] == archive.with_suffix('.zip.sha256').read_text().split()[0]
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            manifest = json.loads(z.read('OUTPUT_MANIFEST.json'))
            for row in manifest['files']:
                assert hashlib.sha256(z.read(row['relpath'])).hexdigest() == row['sha256']
            assert z.read('report/FALSIFIER_REPORT.pdf') == pdf.read_bytes()
        assert pdf.parent == root.parent and archive.parent == root.parent
        assert sha(pdf) == item['report_sha256']
        reports.append({'run_id':item['run_id'], 'output_root':str(out), 'pdf':str(pdf), 'pages':len(reader.pages), 'pdf_sha256':sha(pdf),
                        'archive':str(archive), 'archive_sha256':sha(archive), 'required_sections':14, 'framework_markers':16,
                        'report_data_exact_ledger_match':True, 'framework_generated_tex_exact_match':True, 'plot_data_exact_match':True,
                        'output_manifest_verified':True, 'science_evidence_verified':True, 'zip_verified':True})
    for p,digest in read(OUT/'successful_run1_preservation_pins.json').items():
        assert sha(p) == digest
    before = read(OUT/'PRESERVATION_BEFORE.json')
    assert snapshot(FAMILY/'A011-v0.3.1') == before['A011-v0.3.1']
    assert snapshot(FAMILY/'A011-v0.4.0') == before['A011-v0.4.0']
    assert (FAMILY/'A011-v0.4.0/science_contract.json').read_bytes() == (root/'science_contract.json').read_bytes()
    assert read(root/'config/geometry_smoke_v040.json') == read(FAMILY/'A011-v0.4.0/config/geometry_smoke_v040.json')
    for ref in before['references']:
        assert sha(ROOT/ref['pdf']) == ref['pdf_sha256'] and sha(ROOT/ref['tex']) == ref['tex_sha256']
    create_json(OUT/'REPORT_PACKAGING_GATES_FINAL.json', {'reporting_gate':'PASS', 'packaging_gate':'PASS', 'standalone_run_all_gate':'PASS',
                'repeat_run_retention_gate':'PASS', 'historical_versions_preserved':True, 'science_contract_and_thresholds_unchanged':True,
                'scientific_gate':'UNRESOLVED_MISSING_PHYSICAL_INPUTS', 'scheduled_status':'PAUSED', 'retained_publication_count':retained_count, 'runs':reports})
    print(json.dumps({'reports':reports,'status':'PASS'}, indent=2))


if __name__ == '__main__':
    main()
