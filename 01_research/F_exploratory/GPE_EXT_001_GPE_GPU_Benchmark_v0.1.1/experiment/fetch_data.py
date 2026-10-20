"""Reproducible downloader for openly published processed observations.
No dataset bytes bundled; download is always from the original repository.
"""
from __future__ import annotations
import argparse,hashlib,json,os,time,urllib.request,zipfile
from pathlib import Path

RECORD={
 'name':'Vortex-shedding-PRR-data-1.0.0.zip',
 'record':'https://zenodo.org/records/20068724',
 'doi':'10.5281/zenodo.20068724',
 'url':'https://zenodo.org/records/20068724/files/Vortex-shedding-PRR-data-1.0.0.zip?download=1',
 'md5':'59256e30ecd9e956d911c32f7a16d55b',
 'evidence_class':'processed_observables_only',
 'science_claim':'source integrity only; not a field-level GPE validation'
}

def digest(p,algo):
    h=hashlib.new(algo)
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1<<20),b''):h.update(c)
    return h.hexdigest()

def run(dest:Path,offline=False)->dict:
    dest.mkdir(parents=True,exist_ok=True);path=dest/RECORD['name']
    if not path.exists() and not offline:
        tmp=path.with_suffix(path.suffix+'.part')
        request=urllib.request.Request(RECORD['url'],headers={'User-Agent':'SST-GPE-reference-fetch/0.1 (research; zenodo)'})
        try:
            with urllib.request.urlopen(request,timeout=120) as f, tmp.open('wb') as dst:
                while True:
                    c=f.read(1<<20)
                    if not c:break
                    dst.write(c)
            if digest(tmp,'md5') != RECORD['md5']:
                raise ValueError('Checksum MD5 did not match published Zenodo checksum')
            os.replace(tmp,path)
        finally:
            if tmp.exists():tmp.unlink()
    present=path.is_file()
    verified=present and digest(path,'md5')==RECORD['md5']
    members=[]
    if verified:
        try:
            with zipfile.ZipFile(path) as z:
                if z.testzip() is not None: raise ValueError('ZIP CRC check failed')
                members=[{'name':i.filename,'bytes':i.file_size} for i in z.infolist() if not i.is_dir()]
        except Exception as ex:
            verified=False;members=[{'error':f'{type(ex).__name__}: {ex}'}]
    result={**RECORD,'exists':present,'verified':bool(verified),
            'sha256':digest(path,'sha256') if present else None,
            'bytes':path.stat().st_size if present else 0,'file_count':len(members),
            'members':members,'verification_time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    (dest/'DATA_PROVENANCE.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dest',type=Path,default=Path('data')/'external');p.add_argument('--offline',action='store_true')
    args=p.parse_args();v=run(args.dest,args.offline);print(json.dumps({k:v[k] for k in ('exists','verified','sha256','bytes','file_count')},indent=2));raise SystemExit(0 if v['verified'] else 4)
