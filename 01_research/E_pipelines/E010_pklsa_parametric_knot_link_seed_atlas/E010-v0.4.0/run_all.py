"""Bounded create-only ingestion, offline packaging validation, idempotent verify."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, shutil, subprocess, sys, uuid, zipfile
sys.dont_write_bytecode=True
from build_combined import OUTPUT_NAME, build_payload, verify_payload, read, write
from sst_pklsa.combined_atlas import need, sha, safe_path

ROOT=Path(__file__).resolve().parent

def log_command(command, path, cwd):
    with path.open('xb') as stream:
        result=subprocess.run(command,cwd=cwd,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}); inspect {path}')
    return path.read_text(encoding='utf-8',errors='replace')

def test_suite(run):
    text=log_command([sys.executable,'-B','-m','unittest','discover','-s','tests','-v'],run/'tests.log',ROOT)
    import re
    match=re.search(r'Ran (\d+) tests?',text)
    need(match is not None and '\nOK' in text,'Tests did not complete')
    return int(match[1])

def source_files():
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file()
            and p.relative_to(ROOT).parts[0] in {'sst_pklsa','pklsa_builder','configs','tests'}
            and '__pycache__' not in p.parts} | {
            p.name:sha(p) for p in sorted(ROOT.iterdir()) if p.is_file() and p.suffix in {'.py','.cmd','.md','.txt','.json'}
            and p.name != 'PUBLICATION.json'}

def verify_publication():
    pub=read(ROOT/'PUBLICATION.json')
    need(pub['source_files']==source_files(),'Frozen version source changed')
    result=verify_payload(ROOT/OUTPUT_NAME)
    for entry in pub['artifacts']:
        p=safe_path(ROOT.parent,entry['name'])
        need(p.is_file() and sha(p)==entry['sha256'],'Published artifact changed: '+entry['name'])
    archive=ROOT.parent/pub['zip_name']
    with zipfile.ZipFile(archive) as z:need(z.testzip() is None,'Published ZIP CRC failed')
    result.update(status='PASS_IDEMPOTENT_VERIFICATION',zip_sha256=pub['zip_sha256'])
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('mode',nargs='?',default='BUILD',choices=['BUILD','VERIFY','SELFTEST'])
    ap.add_argument('--workbench',type=Path,default=ROOT.parents[3]);args=ap.parse_args()
    run_id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8]
    run=ROOT/'runs'/run_id;run.mkdir(parents=True,exist_ok=False)
    lock=ROOT/'.build.lock';token=uuid.uuid4().hex
    try:
        with lock.open('x',encoding='utf-8') as f:json.dump({'token':token,'run_id':run_id,'pid':os.getpid()},f)
    except FileExistsError:
        write(run/'RESULT.json',{'status':'SKIPPED_BUSY','run_id':run_id});return 3
    try:
        count=test_suite(run)
        if args.mode=='SELFTEST':result={'status':'PASS_SELFTEST','test_count':count}
        elif (ROOT/'PUBLICATION.json').exists():result=verify_publication()
        elif args.mode=='VERIFY':raise RuntimeError('No completed publication')
        else:
            output=ROOT/OUTPUT_NAME
            need(not output.exists(),'Unexplained existing output without publication')
            zip_name=OUTPUT_NAME+'.zip';pdf_name='SST_Parametric_Knot_Link_Seed_Atlas_v0.4.0_INTAKE_REPORT.pdf'
            for name in [zip_name,zip_name+'.sha256',pdf_name]:need(not (ROOT.parent/name).exists(),'Existing artifact: '+name)
            stage=run/OUTPUT_NAME
            summary=build_payload(args.workbench.resolve(),stage)
            checked=verify_payload(stage)
            archive=run/zip_name
            print('Creating portable ZIP...',flush=True)
            with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
                for p in sorted(stage.rglob('*')):
                    if p.is_file():z.write(p,OUTPUT_NAME+'/'+p.relative_to(stage).as_posix())
            print('Checking ZIP and extracting independent copy...',flush=True)
            extracted=run/'portable_check';extracted.mkdir()
            with zipfile.ZipFile(archive) as z:
                need(z.testzip() is None,'ZIP CRC failure')
                need(len(z.namelist())==len(set(z.namelist())),'ZIP duplicate paths')
                for name in z.namelist():safe_path(extracted,name)
                z.extractall(extracted)
            isolated=extracted/OUTPUT_NAME
            text=log_command([sys.executable,'-I','-B',str(isolated/'verify_atlas.py')],run/'portable_check.log',isolated)
            portable=json.loads(text.strip().splitlines()[-1]);need(portable['status']=='PASS_PORTABLE_ATLAS','Offline check failed')
            digest=sha(archive)
            sidecar=run/(zip_name+'.sha256');sidecar.write_text(digest+'  '+zip_name+'\n',encoding='ascii')
            publication={'schema':'PKLSA-COMBINED-PUBLICATION-1','run_id':run_id,
                'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'timezone':'Europe/Amsterdam','zip_name':zip_name,'zip_sha256':digest,
                'index_sha256':checked['index_sha256'],'test_count':count,
                'portable_loaded_geometries':portable['loaded_geometries'],'source_files':source_files(),
                'scientific':'NOT_RUN'}
            from render_intake import render
            render(run/pdf_name,summary,publication)
            publication['artifacts']=[{'name':name,'sha256':sha(run/name),'bytes':(run/name).stat().st_size}
                                     for name in [zip_name,zip_name+'.sha256',pdf_name]]
            # Recheck the payload and frozen inputs immediately before publication.
            verify_payload(stage)
            from build_combined import verify_sources
            verify_sources(args.workbench.resolve())
            need(publication['source_files']==source_files(),'Source changed during run')
            stage.rename(output)
            for a in publication['artifacts']:
                need(not (ROOT.parent/a['name']).exists(),'Publication race: '+a['name'])
                (run/a['name']).rename(ROOT.parent/a['name'])
            write(ROOT/'PUBLICATION.json',publication)
            result={'status':'PASS_COMBINED_ATLAS_PUBLICATION','record_count':11757,'test_count':count,
                    'zip_sha256':digest,'index_sha256':checked['index_sha256'],
                    'portable_loaded_geometries':portable['loaded_geometries'],'scientific':'NOT_RUN'}
        result['run_id']=run_id;write(run/'RESULT.json',result);print(json.dumps(result,indent=2));return 0
    except Exception as e:
        import traceback
        write(run/'RESULT.json',{'status':'ERROR','run_id':run_id,'error':str(e),'traceback':traceback.format_exc()})
        print(traceback.format_exc(),file=sys.stderr);return 1
    finally:
        if lock.exists() and read(lock).get('token')==token:lock.unlink()

if __name__=='__main__':sys.exit(main())
