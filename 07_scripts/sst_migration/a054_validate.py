"""Validate bounded publications, fail-closed checks and historical preservation."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import zipfile

sys.dont_write_bytecode=True
from preflight import ROOT,read,sha
from a054_prepare import OUT,TARGET,FAMILY
from phase3_prepare import create_json,snapshot


def main():
    from pypdf import PdfReader
    sys.path.insert(0,str(TARGET))
    from a054_state import migration,admission,pklsa
    migration.qualified_framework(TARGET)
    migration.verify_protocol(TARGET)
    from sst_falsifier.report import assert_report,write_auto_science_tex,write_auto_results_tex
    from sst_falsifier.outputs import verify_output_manifest,verify_science_evidence_manifest
    assert_report(TARGET/'report/FALSIFIER_REPORT.tex',require_complete=True)
    history=[json.loads(line) for line in (TARGET/'PUBLICATIONS.jsonl').read_text().splitlines()]
    results=[]
    for item in history[-2:]:
        out=TARGET/f"{item['output_prefix']}_{item['version']}_outputs"
        if read(out/'RUN_ID.json')['run_id']!=item['run_id']:out=out.with_name(out.name+'__'+item['run_id'])
        ledger=read(out/'GATE_LEDGER.json')
        data=read(out/'REPORT_DATA.json')
        assert data['gates']==ledger['records']
        assert data['gate_axes']==item['gate_axes']
        assert data['gate_axes']['scientific_gate']=='NOT_RUN'
        assert all(g['execution_status']=='NOT_EXECUTED' for g in ledger['records'] if g['gate_id'] not in {'G0','G1','G9'})
        assert read(out/'GEOMETRY_RELOADS.json')==data['geometry']
        assert len(data['geometry'])==5
        assert all(r['verified_geometry_sha256']==r['geometry_sha256'] for r in data['geometry'])
        assert all(s['exists'] and s.get('sha256') for s in read(out/'SOURCE_MANIFEST.json')['sources'])
        assert verify_science_evidence_manifest(out,out/'SCIENCE_EVIDENCE_MANIFEST.json')[0]
        assert verify_output_manifest(out,out/'OUTPUT_MANIFEST.json')[0]
        pdf=Path(item['report_pdf']);reader=PdfReader(pdf)
        text='\n'.join(p.extract_text() for p in reader.pages)
        for section in ['Identification','Question','Hypotheses','Assumptions','Symbols','Equations','Algorithm','Sources','Gates and diagnostic','Numerics','Backends','Blindness','Statistics','Results','Interpretation','Reproducibility','References']:
            assert section in text,section
        assert 'exact admitted carrier reloads' in text.lower()
        assert sha(pdf)==item['report_sha256']
        with tempfile.TemporaryDirectory() as temp:
            auto=Path(temp)/'AUTO_RESULTS.tex'
            write_auto_results_tex(TARGET,out,auto)
            assert auto.read_bytes()==(out/'report/AUTO_RESULTS.tex').read_bytes()
            write_auto_science_tex(TARGET,auto)
            assert auto.read_bytes()==(out/'report/AUTO_SCIENCE_CONTRACT.tex').read_bytes()
        archive=Path(item['archive']['zip'])
        assert sha(archive)==item['archive']['sha256']==archive.with_suffix('.zip.sha256').read_text().split()[0]
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for row in json.loads(z.read('OUTPUT_MANIFEST.json'))['files']:
                assert hashlib.sha256(z.read(row['relpath'])).hexdigest()==row['sha256']
            assert z.read('report/FALSIFIER_REPORT.pdf')==pdf.read_bytes()
        results.append({'run_id':item['run_id'],'pages':len(reader.pages),'pdf_sha256':sha(pdf),'zip_sha256':sha(archive),'exact_ledger_match':True,'source_manifest_valid':True,'scientific_gate':'NOT_RUN'})
    # Every earlier publication remains readable and hash-identical.
    for item in history:
        assert sha(Path(item['report_pdf']))==item['report_sha256']
        assert sha(Path(item['archive']['zip']))==item['archive']['sha256']
    pins=read(TARGET/'admission/RUNTIME_PINS.json')
    manifest=TARGET/'admission/CROSS_CARRIER_MANIFEST.json'
    checks=[]
    original=admission.digest
    source=Path(read(manifest)['carriers'][0]['source_locator']['source_path'])
    admission.digest=lambda p:'0'*64 if Path(p).resolve()==source.resolve() else original(p)
    try:
        admission.validate_manifest(manifest,ROOT,pins)
        raise AssertionError('raw tamper accepted')
    except admission.AdmissionError as e:
        assert 'raw geometry hash mismatch' in str(e);checks.append('RAW_PAYLOAD_DRIFT_REJECTED')
    finally:admission.digest=original
    original_geometry=pklsa.geometry_sha256
    pklsa.geometry_sha256=lambda components:'0'*64
    try:
        pklsa._load_manifest_geometry(read(manifest)['carriers'][0],ROOT/pins['e010_root'],ROOT)
        raise AssertionError('parsed geometry tamper accepted')
    except ValueError as e:
        assert 'geometry_sha256 mismatch' in str(e);checks.append('PARSED_GEOMETRY_DRIFT_REJECTED')
    finally:pklsa.geometry_sha256=original_geometry
    before=read(OUT/'PRESERVATION_BEFORE.json')
    assert snapshot(FAMILY/'A054-v0.5.1')==before['A054-v0.5.1']
    assert sha(FAMILY/'FAMILY.yaml')==before['family_sha256']
    with zipfile.ZipFile(read(OUT/'SOURCE_ADMISSION.json')['source_archive']) as z:
        m=next(n for n in z.namelist() if n.endswith('/PACKAGE_MANIFEST.json'));prefix=m[:-len('PACKAGE_MANIFEST.json')]
        old_science=json.loads(z.read(prefix+'science_contract.json'));new_science=read(TARGET/'science_contract.json')
        old_science.pop('implementation_commitment');new_science.pop('implementation_commitment')
        assert json.loads(json.dumps(old_science).replace('v0.5.1','v0.6.0'))==new_science
        for rel in ['configs/basic.json','configs/full.json','configs/certify.json','native_ext/a054_native.cpp','native_ext/energy_core.hpp']:
            assert z.read(prefix+rel)==(TARGET/rel).read_bytes()
    assert sha(ROOT/'01_research/A_falsifiers/A011_maxwell_1_kinetic_energy/A011-v0.4.1/LATEST_RUN.json')==before['A011_latest_sha256']
    assert sha(ROOT/'01_research/A_falsifiers/A065_Triadic_Casimir_Blind/FAMILY.yaml')==before['A065_family_sha256']
    record={'status':'PASS_BOUNDED_MIGRATION','tests_per_final_run':36,'final_runs':results,'retained_publications':len(history),
            'scientific_contract_unchanged_except_implementation_commitment_and_version_references':True,'thresholds_and_native_kernels_byte_identical':True,
            'historical_parent_unchanged':True,'negative_runtime_checks':checks,'source_gate':'PASS_EXPLICIT_USER_ADMISSION_59_FILES',
            'migration_gate':'PASS_SOURCE_AND_ADAPTER','execution_gate':'PASS_BOUNDED_ADMISSION_SMOKE','scientific_gate':'NOT_RUN',
            'reporting_gate':'PASS','packaging_gate':'PASS','repeat_run_gate':'PASS','scheduled_status':'ACTIVE',
            'remaining':['One selected provider per BASIC topology; no cross-provider closure','State selection, stationarity, Hessian, ringdown and native parity not executed','Full scientific and E013 campaign release remains closed','Source ZIP lacks independent publisher signature; explicit bounded user admission retained']}
    create_json(OUT/'gate_overview.json',record)
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
