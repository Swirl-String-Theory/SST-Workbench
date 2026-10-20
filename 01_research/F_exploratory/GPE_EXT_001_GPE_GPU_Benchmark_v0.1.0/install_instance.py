"""Install a real SST Falsifier Framework v1.0.10 instance without modifying upstream."""
from __future__ import annotations
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
INSTANCE_NAME='GPE_GPU_Benchmark'
VERSION='v0.1.1'
CATALOG_ID='GPE_EXT_001'  # provisional ID, not a registered A-number
FRAMEWORK_DIR='SST_Falsifier_Framework_v1.0.10'


def dump(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def install(workbench:Path|None,destination:Path|None):
    wb=(workbench or Path(os.environ.get('SST_WORKBENCH_ROOT',r'C:\workspace\projects\SST-Workbench'))).resolve()
    framework=wb/'06_templates'/'SST_Falsifier_Framework'/FRAMEWORK_DIR
    if not (framework/'sst_falsifier'/'__init__.py').is_file() or not (framework/'tools'/'new_falsifier.py').is_file():
        raise SystemExit(f'Framework v1.0.10 not found at {framework}. No downgrade or fallback allowed.')
    info=framework/'RELEASE_INFO.json'
    if not info.exists() or json.loads(info.read_text(encoding='utf8')).get('version')!='1.0.10':
        raise SystemExit('Framework release marker missing/mismatched (requires exact 1.0.10).')
    dst=(destination or (wb/'01_research'/'F_exploratory'/f'{CATALOG_ID}_{INSTANCE_NAME}_{VERSION}')).resolve()
    dst.parent.mkdir(parents=True,exist_ok=True)
    stamp=dst/'GPE_INSTALL_MANIFEST.json'
    if dst.exists():
        if stamp.is_file() and json.loads(stamp.read_text(encoding='utf-8')).get('schema')=='GPE-INSTALL-MANIFEST-1':
            print(f'Existing installation: {dst}');return dst
        raise SystemExit(f'Destination exists but is not managed by this installer: {dst}')
    cmd=[sys.executable,str(framework/'tools'/'new_falsifier.py'),CATALOG_ID,INSTANCE_NAME,str(dst),'--profile','gpu','--version',VERSION]
    subprocess.run(cmd,cwd=framework,check=True)
    (dst/'experiment').mkdir(exist_ok=True)
    for n in ('gpe_engine.py','fetch_data.py','pipeline.py'):
        shutil.copy2(HERE/'payload'/n,dst/'experiment'/n)
    (dst/'tests').mkdir(exist_ok=True)
    for test_name in ('test_gpe.py','test_fetch.py'):
        shutil.copy2(HERE/'tests'/test_name,dst/'tests'/test_name)
    (dst/'run_all.cmd').write_bytes((HERE/'payload'/'instance_run_all.cmd').read_bytes())
    shutil.copy2(HERE/'payload'/'preflight_report.py',dst/'preflight_report.py')
    (dst/'requirements_gpe.txt').write_text('numpy>=2.0,<3\n','utf-8')
    original_toml=(dst/'falsifier.toml').read_text(encoding='utf-8')
    if 'pdf_required = false' not in original_toml:
        raise SystemExit('Expected framework template report policy not found; refusing unsafe blind rewrite.')
    original_toml=original_toml.replace('pdf_required = false','pdf_required = true',1)
    (dst/'falsifier.toml').write_text(original_toml+'''
# GPE uses torch.xpu, NOT the native C++ or framework SYCL GPE solver.
[backends.cpp]
enabled = false
[backends.sycl]
enabled = true
authority = "SCREENING_ONLY"
precision = "float32"
[sources]
multilibrary_required = false
independent_confirmation_required = false
''',encoding='utf-8')
    # Readable report and contract: complete before FREEZE.
    shutil.copy2(HERE/'payload'/'FALSIFIER_REPORT.tex',dst/'report'/'FALSIFIER_REPORT.tex')
    shutil.copy2(HERE/'payload'/'science_contract.json',dst/'science_contract.json')
    # File paths in the framework source resolver are relative to SST_WORKBENCH_ROOT.
    external=dst/'data'/'external'/'Vortex-shedding-PRR-data-1.0.0.zip'
    try:relative=external.relative_to(wb).as_posix()
    except ValueError:
        raise SystemExit('Destination must lie under the SST-Workbench root for source provenance correctness.')
    dump(dst/'source_contract.json',{
        'schema':'SST-SOURCE-CONTRACT-2','independent_unit':'published Zenodo archive, not independent raw wavefunction field',
        'sources':[{'source_id':'ZENODO-20068724','catalog_id':'PUBLIC-ZENODO-20068724',
            'version':'v1.0.0','relative_path':relative,'role':'external processed-observable source',
            'independence_family':'Kwon-Shin-vortex-shedding',
            'provenance_family':'Zenodo-20068724','evidence_class':'independent_source'}],
        'parser_contract':'ZIP integrity and metadata only; no comparability claim for processed observables',
        'translator_contract':'No dimensional mapping to PKLSA or SST',
        'allow_no_external_sources':False,
        'replication_policy':{'require_explicit_evidence_class':True,'min_independent_groups':2,
                              'synthetic_controls_may_close_cross_source':False}})
    gates=json.loads((dst/'gate_plan.json').read_text(encoding='utf8'))
    meanings={
        'G0':'Frozen protocol and v1.0.10 runtime verified?',
        'G1':'Is the external Zenodo processed-observable archive checksum and CRC verified?',
        'G2':'Does an independent NumPy-FP64 GPE TSSP pass plane-wave, norm and time-reversal checks?',
        'G3':'Is second-order time-step convergence demonstrated without using physical field labels?',
        'G4':'Is there a separate field-level independent research dataset confirmation? (disabled pending comparable fields)',
        'G5':'Does an independent native C++ FP64 GPE solver certify parity? (disabled: unavailable)',
        'G6':'Does the Intel XPU real GPU solver agree with NumPy FP64 under preregistered screening thresholds?',
        'G7':'Do multiple independent sources replicate? (disabled pending data mapping)',
        'G8':'Does genuine PKLSA/Euler vortex mechanism reproduce GPE measurements? (unimplemented)',
        'G9':'Separate blind reveal integrity verification (not an automatic physical claim)'
    }
    for g in gates['gates']:
        gid=g['gate_id'];g['question']=meanings[gid]
        if gid=='G2':g['requires']=['G0'] # Numerical reference is independent of external processed observations.
        if gid=='G6':g['requires']=['G2'] # Torch XPU screening requires CPU analytic gate, not disabled native C++.
        if gid=='G3':g['requires']=['G2'] # benchmark convergence is independent from external archive integrity.
        if gid=='G8':g['requires']=['G3','G6']
    dump(dst/'gate_plan.json',gates)
    # Reuse only byte-verified published data. Never copy frozen protocol, gates,
    # reports or identity files from a prior instance into this new version.
    prior=dst.parent/f'{CATALOG_ID}_{INSTANCE_NAME}_v0.1.0'
    previous_zip=prior/'data'/'external'/'Vortex-shedding-PRR-data-1.0.0.zip'
    if previous_zip.is_file():
        import hashlib
        h=hashlib.md5()
        h256=hashlib.sha256()
        with previous_zip.open('rb') as handle:
            for chunk in iter(lambda:handle.read(1<<20),b''):
                h.update(chunk)
                h256.update(chunk)
        if (h.hexdigest()=='59256e30ecd9e956d911c32f7a16d55b'
                and h256.hexdigest()=='69a58532fc01a013a2a7ba17428787f68e2c62b4a5181cee4e822092d7aa5b9e'):
            new_data=dst/'data'/'external'
            new_data.mkdir(parents=True,exist_ok=True)
            shutil.copy2(previous_zip,new_data/previous_zip.name)
            # This manifest is regenerated during run_all.cmd DATA/BASIC/FULL.
            print('Reused validated Zenodo archive from v0.1.0:',previous_zip)
        else:
            print('WARNING: v0.1.0 archive checksum invalid; will download independently')
    dump(stamp,{'schema':'GPE-INSTALL-MANIFEST-1','framework_version':'1.0.10',
                'framework_status':'LOCAL_VALIDATED_CANDIDATE_AT_PACKAGING',
                'catalog_id':CATALOG_ID,'version':VERSION,
                'status':'DEVELOPMENT_NOT_FROZEN_UNTIL_LOCAL_RUN','installer':'GPE-GPU v0.1.1',
                'description':'Generated from unmodified v1.0.10 framework; GPU uses torch.xpu.'})
    print('Instance generated:',dst)
    print('Start: cd /d "'+str(dst)+'" && run_all.cmd BASIC')
    return dst

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workbench',type=Path);p.add_argument('--destination',type=Path)
    args=p.parse_args();install(args.workbench,args.destination)
