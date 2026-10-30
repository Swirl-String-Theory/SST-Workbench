"""True subprocess isolation E2E: frozen source not installed, 2/3 gate BLOCKED."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile,zipfile
from sst_falsifier.report import REQUIRED_SECTION_MARKERS
from sst_falsifier.outputs import verify_output_manifest
root_framework=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='sst_v1100_standalone_') as td:
    root=Path(td)/'A999-v0.1.0'
    cp=subprocess.run([sys.executable,str(root_framework/'tools'/'new_falsifier.py'),'A999','isolated',str(root)],capture_output=True,text=True)
    assert cp.returncode==0,cp.stderr
    def clean(a):
        if isinstance(a,str):return a.replace('REPLACE_BEFORE_FREEZE','standalone software diagnostic control')
        if isinstance(a,list):return [clean(v) for v in a]
        if isinstance(a,dict):return {k:clean(v) for k,v in a.items()}
        return a
    sc=root/'science_contract.json';sc.write_text(json.dumps(clean(json.loads(sc.read_text())),indent=2))
    source=root/'source_contract.json';x=clean(json.loads(source.read_text()));x['sources']=[];x['allow_no_external_sources']=True;source.write_text(json.dumps(x,indent=2))
    tex='\\documentclass{article}\n\\usepackage{longtable,booktabs}\n\\begin{document}\nTest study — unqualified.\n'
    tex+='\n'.join('% SST-REPORT-SECTION:'+m+'\n\\section{'+m.title()+'}\nSynthetic software control with a fixed protocol. No physical inference or accepted backend certification is claimed for this diagnostic control.' for m in REQUIRED_SECTION_MARKERS)
    tex+='\n\\input{AUTO_SCIENCE_CONTRACT.tex}\n\\input{AUTO_RESULTS.tex}\n\\end{document}\n'
    (root/'report'/'FALSIFIER_REPORT.tex').write_text(tex,encoding='utf8')
    env=dict(os.environ);env['PYTHONPATH']='';env['SST_FALSIFIER_FRAMEWORK_ROOT']='/nonexistent-old-framework'
    def run(mode,expect):
        cp=subprocess.run([sys.executable,'run_instance.py',mode],cwd=root,env=env,capture_output=True,text=True)
        assert cp.returncode==expect,(mode,cp.stdout[-2400:],cp.stderr[-2400:]);return cp
    run('FREEZE',0)
    run('FULL',3)
    out=root/'isolated_v0.1.0-outputs'
    assert json.loads((out/'AUTO_BACKEND_MATRIX.json').read_text())['counted_backend_categories']==0
    assert verify_output_manifest(out,out/'OUTPUT_MANIFEST.json')[0]
    pdfs=list(Path(td).glob('*FALSIFIER_REPORT.pdf'))
    zips=list(Path(td).glob('*BLIND.zip'))
    assert len(pdfs)==1 and len(zips)==1
    assert pdfs[0].read_bytes().startswith(b'%PDF-')
    sidecar=zips[0].with_suffix('.zip.sha256');assert sidecar.exists()
    assert sidecar.read_text().split()[0]==hashlib.sha256(zips[0].read_bytes()).hexdigest()
    with zipfile.ZipFile(zips[0]) as z:assert z.testzip() is None
    assert not (root/'.sst_framework_root').exists()
    print(json.dumps({'status':'PASS','mode':'FULL','exit_code':3,'backend_gate':'BLOCKED_AS_DESIGNED',
      'local_framework_root':str(root/'_sst_runtime'),'pdf_bytes':pdfs[0].stat().st_size,
      'zip_bytes':zips[0].stat().st_size,'report_qualified':False},indent=2))
