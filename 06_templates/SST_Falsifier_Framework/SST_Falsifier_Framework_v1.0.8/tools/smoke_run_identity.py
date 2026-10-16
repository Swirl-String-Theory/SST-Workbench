"""Real end-to-end local smoke for two runs with PDF + preserved ZIP evidence."""
from pathlib import Path
import json
import tempfile
import subprocess
import sys
from sst_falsifier.runner import run_mode
from sst_falsifier.output_policy import read_run_id, report_path, package_path
from sst_falsifier.report import REQUIRED_SECTION_MARKERS

framework=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='sst_export_smoke_') as td:
    root=Path(td)/'A888-v0.0.1'
    cp=subprocess.run([sys.executable,str(framework/'tools/new_falsifier.py'),'A888','Example',str(root),'--profile','minimal'],capture_output=True,text=True)
    if cp.returncode: raise RuntimeError(cp.stderr)
    science=json.loads((root/'science_contract.json').read_text())
    def clean(x):
        if isinstance(x,str): return 'controlled synthetic smoke' if 'REPLACE_BEFORE_FREEZE' in x else x
        if isinstance(x,list):return [clean(v) for v in x]
        if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
        return x
    (root/'science_contract.json').write_text(json.dumps(clean(science)),encoding='utf-8')
    source=json.loads((root/'source_contract.json').read_text())
    source['sources']=[];source['allow_no_external_sources']=True
    (root/'source_contract.json').write_text(json.dumps(clean(source)),encoding='utf-8')
    tex='\\documentclass{article}\n\\usepackage{longtable,booktabs}\n\\begin{document}\nSmoke.\n'
    tex+='\n'.join(f'% SST-REPORT-SECTION:{name}' for name in REQUIRED_SECTION_MARKERS)
    tex+='\n\\input{AUTO_SCIENCE_CONTRACT.tex}\n\\input{AUTO_RESULTS.tex}\n\\end{document}\n'
    (root/'report/FALSIFIER_REPORT.tex').write_text(tex,encoding='utf-8')
    rc=run_mode(root,'FREEZE'); assert rc==0
    p={'project':{'name':'Example','version':'v0.1.0'}}
    # version is generated --version default v0.1.0
    out=root/'Example_v0.1.0-outputs'
    rc=run_mode(root,'BASIC');assert rc==0
    r1=read_run_id(out); z1=package_path(root,p,r1,'BLIND');pdf1=report_path(root,r1,'BLIND')
    assert z1.is_file() and pdf1.is_file(),(z1,pdf1)
    data1=z1.read_bytes(); pdf_data=pdf1.read_bytes()
    rc=run_mode(root,'BASIC');assert rc==0
    r2=read_run_id(out);z2=package_path(root,p,r2,'BLIND');pdf2=report_path(root,r2,'BLIND')
    assert r1!=r2 and z1.is_file() and pdf1.is_file() and z2.is_file() and pdf2.is_file()
    assert z1.read_bytes()==data1 and pdf1.read_bytes()==pdf_data
    archive=root/f'Example_v0.1.0-outputs__{r1}'
    assert archive.is_dir() and (archive/'OUTPUT_MANIFEST.json').is_file()
    # Fresh run's source scan excluded old run snapshot.
    print(json.dumps({'status':'PASS','runs':[r1,r2],'pdfs':2,'blind_zips':2,'archived_previous':True,'pdf1_bytes':len(pdf_data),'pdf2_bytes':pdf2.stat().st_size},indent=2))
