from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, shutil, tempfile, zipfile

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_SOURCE=ROOT.parent/'A058-v0.1.3'

def sha256_file(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def copy_campaign(src_campaign:Path):
    required=['manifest_pilot.json','runtime_pilot.json','runlog_pilot.json','results']
    for name in required:
        if not (src_campaign/name).exists():
            raise SystemExit(f'Missing upstream campaign artifact: {src_campaign/name}')
    man=json.loads((src_campaign/'manifest_pilot.json').read_text(encoding='utf-8'))
    runlog=json.loads((src_campaign/'runlog_pilot.json').read_text(encoding='utf-8'))
    if len(man.get('conditions',[]))!=150:
        raise SystemExit(f'Expected 150 upstream pilot conditions, got {len(man.get("conditions",[]))}')
    if len(runlog)!=150 or any(int(r.get('returncode',1))!=0 for r in runlog):
        raise SystemExit('Upstream runlog is incomplete or contains non-zero KnotPlot exits.')

    cfg=json.loads((ROOT/'configs/default.json').read_text(encoding='utf-8'))
    cps=[int(x) for x in cfg['checkpoints']]
    missing=[]
    for c in man['conditions']:
        cid=c['condition_id']
        for cp in cps:
            p=src_campaign/'results'/cid/f'i{cp:06d}.txt'
            if not p.is_file() or p.stat().st_size==0: missing.append(str(p))
    if missing:
        raise SystemExit(f'Upstream coordinate acquisition incomplete; first missing: {missing[:5]}')

    dest=ROOT/'campaign'
    for name in ['results','manifest_pilot.json','runtime_pilot.json','runlog_pilot.json','active_tier.json']:
        p=dest/name
        if p.is_dir(): shutil.rmtree(p)
        elif p.exists(): p.unlink()
    shutil.copytree(src_campaign/'results',dest/'results')
    for name in ['manifest_pilot.json','runtime_pilot.json','runlog_pilot.json']:
        shutil.copy2(src_campaign/name,dest/name)
    (dest/'active_tier.json').write_text(json.dumps({'tier':'pilot'},indent=2)+'\n',encoding='utf-8')

    files=[]
    for p in sorted((dest/'results').rglob('*')):
        if p.is_file():
            files.append({'path':p.relative_to(ROOT).as_posix(),'size':p.stat().st_size,'sha256':sha256_file(p)})
    payload={
      'schema':'A058-UPSTREAM-IMPORT-1',
      'source_version':'v0.1.3',
      'source_campaign':str(src_campaign.resolve()),
      'condition_count':150,
      'runlog_nonzero_exits':0,
      'coordinate_file_count':sum(1 for f in files if f['path'].endswith('.txt')),
      'metrics_csv_nonempty':sum(1 for f in files if f['path'].endswith('metrics.csv') and f['size']>0),
      'files':files,
    }
    payload['files_manifest_sha256']=hashlib.sha256(
      json.dumps(files,sort_keys=True,separators=(',',':')).encode('utf-8')
    ).hexdigest()
    (dest/'UPSTREAM_IMPORT.json').write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(f'Imported v0.1.3 pilot: 150 conditions; {payload["coordinate_file_count"]} coordinate files; {payload["metrics_csv_nonempty"]} non-empty metrics CSV files')
    print(f'Import manifest SHA-256: {payload["files_manifest_sha256"]}')

def main():
    ap=argparse.ArgumentParser(description='Import the completed A058-v0.1.3 pilot acquisition read-only into v0.1.4 recovery analysis.')
    ap.add_argument('--source',default=str(DEFAULT_SOURCE),help='A058-v0.1.3 instance folder or v0.1.3 outputs ZIP')
    a=ap.parse_args()
    src=Path(a.source).expanduser().resolve()
    if src.is_dir():
        camp=src/'campaign' if (src/'campaign').is_dir() else src
        copy_campaign(camp); return
    if src.is_file() and src.suffix.lower()=='.zip':
        with tempfile.TemporaryDirectory(prefix='a058_v013_import_') as td:
            with zipfile.ZipFile(src) as z: z.extractall(td)
            base=Path(td)
            candidates=[p for p in base.rglob('campaign') if (p/'manifest_pilot.json').is_file()]
            if not candidates: raise SystemExit('Could not find campaign/manifest_pilot.json in ZIP')
            copy_campaign(candidates[0]); return
    raise SystemExit(f'Unsupported/missing source: {src}')

if __name__=='__main__': main()
