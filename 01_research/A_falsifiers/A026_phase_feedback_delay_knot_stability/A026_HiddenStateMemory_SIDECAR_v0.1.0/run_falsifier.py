"""Executable standalone sidecar; never reports physical SST certification."""
import argparse, datetime as dt, hashlib, json, os, shutil, subprocess, sys, zipfile
from pathlib import Path
import numpy as np
from src.model import synthetic
from src.analysis import compare
from src.intake import read_external
from src.reporting import SECTIONS, render_pdf

ROOT=Path(__file__).resolve().parent
PREFIX='A026_HiddenStateMemory'; VERSION='v0.1.0'

def hash_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def source_manifest():
    return {str(p.relative_to(ROOT)).replace('\\','/'):hash_file(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and '.pytest_cache' not in p.parts and '__pycache__' not in p.parts and not p.name.endswith('.pyc')}

def run_basic():
    c=synthetic(n=1500, coupling=2.0)
    n=synthetic(n=1500, coupling=0.0)
    rc=compare(c); rn=compare(n)
    shuffled=dict(c); shuffled['history']=c['history'][np.random.default_rng(20261030).permutation(len(c['target']))]
    rs=compare(shuffled)
    err=max(abs(c['final_energy']-c['initial_energy'])/c['initial_energy'])
    gates={
        'G0':{'status':'PASS' if err < 1e-12 else 'FAIL','reason':f'Exact Hamiltonian energy max relative error {err:.3e}'},
        'G1':{'status':'PASS' if rn['ci95_gain'][1]<.05 else 'FAIL','reason':'Decoupled null: gain upper 95% < 0.05'},
        'G2':{'status':'PASS' if rc['ci95_gain'][0]>.20 else 'FAIL','reason':'Coupled positive: gain lower 95% > 0.20'},
        'G2B':{'status':'PASS' if rs['ci95_gain'][1]<.05 else 'FAIL','reason':'Randomly permuted history must not improve the independent holdout prediction'},
        'G3':{'status':'PASS' if abs(rc['rmse_history_m']/rc['rmse_full_state_oracle_m']-1)<.05 else 'FAIL','reason':'Full-state oracle closes the hidden-mode information gap in the synthetic linear system'},
        'G4':{'status':'NOT_EXECUTED','reason':'No 3D Euler model/provider or dynamic background core supplied'},
        'G5':{'status':'NOT_EXECUTED','reason':'Spatial, time, finite-core and box convergence missing'},
        'G6':{'status':'NOT_EXECUTED','reason':'Native Euler energy, circulation, helicity, topology not independently measured'},
        'G7':{'status':'NOT_EXECUTED','reason':'No phase-locked intrinsic clock, no operational tau measurement'},
        'G8':{'status':'NOT_EXECUTED','reason':'No independently executed scientific 2-of-3 backend parity'},
        'G9':{'status':'NOT_APPLICABLE','reason':'No reveal targets; no secret labels or fitted SST constants'} }
    return {'case_coupled':rc,'case_decoupled':rn,'case_history_shuffled':rs,'energy_relmax':float(err)},gates,None

def run_external(path):
    data,prov=read_external(path); res=compare(data)
    gates={
        'G0':{'status':'PASS','reason':'NPZ schema/independent trial IDs/declared source metadata valid (metadata not independently authenticated)'},
        'G1':{'status':'PASS' if res['ci95_gain'][0]>.05 else 'NO_SIGNAL','reason':'Held-out extra prediction from history at fixed observed features; diagnostic only'},
        'G2':{'status':'NOT_EXECUTED','reason':'Missing a matched history-shuffle and independent same-state control from native simulation'},
        'G3':{'status':'NOT_EXECUTED','reason':'No full background state oracle to check sufficiency'},
        'G4':{'status':'UNRESOLVED','reason':'Physical Euler solver and material state not independently verified'},
        'G5':{'status':'UNRESOLVED','reason':'No spatial/time/core/domain convergence chain verified'},
        'G6':{'status':'UNRESOLVED','reason':'No independent energy/circulation/helicity/topology gate'},
        'G7':{'status':'NOT_EXECUTED','reason':'No independent intrinsic phase clock qualification'},
        'G8':{'status':'NOT_EXECUTED','reason':'No real second backend parity'},
        'G9':{'status':'NOT_APPLICABLE','reason':'No reveal task in this sidecar'}}
    return {'case_external_unqualified':res},gates,prov

def write_report(run,ledger,results):
    out=run/'A026_HiddenStateMemory_v0.1.0_FALSIFIER_REPORT.md'
    lines=['# A026 - Hidden-State Memory & Backreaction','',
           '**Status: DEVELOPMENT_ONLY / PHYSICAL_EULER_UNRESOLVED / SWIRL_CLOCK_NOT_TESTED.**','',
           'This standalone sidecar report is not an official Framework v1.1.0 RC2 report.','']
    for title,body in SECTIONS:
        lines+=['## '+title,'',body,'']
        if title.startswith('13.'):
            lines+=['```json',json.dumps({'gates':ledger['gates'],'results':results},indent=2),'```','']
    out.write_text('\n'.join(lines),encoding='utf-8')
    pdf=run/'A026_HiddenStateMemory_v0.1.0_FALSIFIER_REPORT.pdf'
    if not render_pdf(pdf,ledger,results):
        (run/'PDF_NOT_RENDERED.txt').write_text('Install reportlab; PDF is optional and never an official framework report.\n')
        return out,None
    return out,pdf

def package_zip(output_root, report_pdf):
    parent=ROOT.parent
    archive=parent/f'{PREFIX}_{VERSION}_outputs.zip'
    if archive.exists():
        archive=parent/f'{PREFIX}_{VERSION}_outputs_{dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")}.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted(output_root.rglob('*')):
            if f.is_file(): z.write(f, f.relative_to(parent))
    (Path(str(archive)+'.sha256')).write_text(f'{hash_file(archive)}  {archive.name}\n',encoding='ascii')
    if report_pdf:
        outside=parent/f'{PREFIX}_{VERSION}_FALSIFIER_REPORT_{dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")}.pdf'
        shutil.copy2(report_pdf,outside)
    return archive

def main(argv=None):
    p=argparse.ArgumentParser(description='Development sidecar for memory-vs-current-state predictive falsification')
    p.add_argument('mode',choices=['TEST','BASIC','EULER','FULL'],nargs='?',default='BASIC')
    p.add_argument('--input',help='External multi-trial NPZ; required for EULER or FULL')
    a=p.parse_args(argv)
    if a.mode=='TEST': return subprocess.call([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT)
    if a.mode=='FULL' and not a.input:
        print('BLOCKED (exit 3): FULL needs independent native Euler NPZ input; no synthesis substituted.');return 3
    if a.mode=='EULER' and not a.input:
        p.error('EULER requires --input')
    result,gates,prov=(run_basic() if a.mode=='BASIC' else run_external(a.input))
    output_root=ROOT.parent/f'{PREFIX}_{VERSION}-outputs'
    run_id=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run=output_root/run_id;run.mkdir(parents=True,exist_ok=False)
    ledger={'schema':'sst.hsm.sidecar.v1','run_id':run_id,'mode':a.mode,
         'status':'DEVELOPMENT_ONLY_PHYSICAL_EULER_UNRESOLVED_SWIRL_CLOCK_NOT_TESTED',
         'framework_status':'NOT_AN_OFFICIAL_SST_FRAMEWORK_V1_1_0_RC2_INSTANCE',
         'gates':gates, 'source_hashes':source_manifest(),
         'source_document_doi':'10.1038/s41567-026-03442-w',
         'reference_family':'A026-v0.2.1','external_provider':prov}
    (run/'GATE_LEDGER.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False),encoding='utf-8')
    (run/'MEASUREMENTS.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    md,pdf=write_report(run,ledger,result)
    archive=package_zip(output_root,pdf)
    print(json.dumps({'diagnostic_results':result,'gates':gates,'output_root':str(run),'report':str(md),
              'pdf':str(pdf) if pdf else None,'archive':str(archive),'archive_sha256':hash_file(archive)},indent=2))
    return 0 if a.mode=='BASIC' else 3 # external science always blocked

if __name__=='__main__': raise SystemExit(main())
