"""Scoped registration using canonical builders; preserve other dirty families."""
from copy import deepcopy
from pathlib import Path
import hashlib, json, os, sys, uuid
ROOT=Path(__file__).resolve().parents[3]
AUDIT=Path(__file__).resolve().parent
FAMILY=ROOT/'01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas'
VERSION=FAMILY/'E010-v0.4.0'
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'07_scripts'))
import build_catalog_index as bci
import build_family_hierarchy as bh

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def read(p):return json.loads(p.read_text(encoding='utf-8'))

def atomic(path,data):
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    with temporary.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.replace(temporary,path)

def encoded(obj):return (json.dumps(obj,indent=2,ensure_ascii=False)+'\n').encode('utf-8')

def main():
    assert not (AUDIT/'REGISTRATION.json').exists()
    pub=read(VERSION/'PUBLICATION.json')
    visual=read(AUDIT/'PDF_VISUAL_QA.json')
    assert visual['status']=='PASS' and visual['pdf_sha256']==next(a['sha256'] for a in pub['artifacts'] if a['name'].endswith('.pdf'))
    repeats=[read(p) for p in (VERSION/'runs').glob('*/RESULT.json')]
    assert any(x['status']=='PASS_IDEMPOTENT_VERIFICATION' for x in repeats)
    files=[FAMILY/'FAMILY.yaml',ROOT/'10_docs/registry/catalog_index.json',ROOT/'10_docs/registry/family_hierarchy.json']
    before={p: p.read_bytes() for p in files}
    for p in files:
        assert before[p] == (AUDIT/'before'/p.relative_to(ROOT)).read_bytes(), f'Concurrent registry change: {p}'
    f,c,h=files
    text=before[f].decode('utf-8')
    assert 'v0.4.0' not in text
    addition='  - id: v0.4.0\n    directory: "E010-v0.4.0"\n    note: "Combined portable intake; historical statuses preserved; Ruban research-only; no new science qualification"\n    publication_manifest: "E010-v0.4.0/PUBLICATION.json"\n'
    newtext=text.replace('variants: []',addition+'variants: []',1)
    assert newtext!=text and newtext.split('latest: ')[1].splitlines()[0]==text.split('latest: ')[1].splitlines()[0]
    atomic(f,newtext.encode('utf-8'))
    generated_c=bci.build();generated_h=bh.build(ROOT)
    oldc=json.loads(before[c]);oldh=json.loads(before[h]);newc=deepcopy(oldc);newh=deepcopy(oldh)
    newc['by_domain']['01_research']['E010']=generated_c['by_domain']['01_research']['E010']
    newc['versions']=oldc['versions']+1
    oldnode=oldh['hierarchy']['01_research']['E_pipelines']['E010']
    newnode=generated_h['hierarchy']['01_research']['E_pipelines']['E010']
    newh['hierarchy']['01_research']['E_pipelines']['E010']=newnode
    newh['by_catalog_id']['E010']=generated_h['by_catalog_id']['E010']
    newh['version_count_declared']=oldh['version_count_declared']+1
    newh['version_count_on_disk']=oldh['version_count_on_disk']+len(newnode['versions_on_disk'])-len(oldnode['versions_on_disk'])
    newh['generated_at']=generated_h['generated_at']
    assert newc['by_domain']['01_research']['E010']['latest']==oldc['by_domain']['01_research']['E010']['latest']
    assert c.read_bytes()==before[c] and h.read_bytes()==before[h]
    atomic(c,encoded(newc));atomic(h,encoded(newh))
    # Explicitly prove all other catalog/family nodes are unchanged.
    cc=deepcopy(newc);cc['by_domain']['01_research']['E010']=oldc['by_domain']['01_research']['E010'];cc['versions']=oldc['versions']
    assert cc==oldc
    hh=deepcopy(newh);hh['hierarchy']['01_research']['E_pipelines']['E010']=oldnode
    hh['by_catalog_id']['E010']=oldh['by_catalog_id']['E010']
    for key in ['version_count_declared','version_count_on_disk','generated_at']:hh[key]=oldh[key]
    assert hh==oldh
    assert bci.parse_family(f)==read(c)['by_domain']['01_research']['E010']
    result={'status':'PASS_SCOPED_REGISTRATION','latest_preserved':newnode['latest'],
            'other_families_unchanged':True,'scientific_status_promoted':False,
            'files':[{'path':p.relative_to(ROOT).as_posix(),'before_sha256':hashlib.sha256(before[p]).hexdigest(),
                      'after_sha256':sha(p)} for p in files]}
    with (AUDIT/'REGISTRATION.json').open('x',encoding='utf-8') as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
