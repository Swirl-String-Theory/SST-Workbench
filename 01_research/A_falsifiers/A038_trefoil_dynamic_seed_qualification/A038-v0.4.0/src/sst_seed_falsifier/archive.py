"""Shareable output archives with an explicit blind/revealed boundary."""
from __future__ import annotations
import argparse, hashlib, json, zipfile
from pathlib import Path

PRIVATE_DIR_NAMES={'sealed','private'}
PRIVATE_FILE_NAMES={
    'blind_key.bin','source_group_key.bin','identity_map.json','source_group_map.json',
    'source_generation_audit.json','EVIDENCE_MANIFEST_PRIVATE.json','private_refine_map.json',
}

def _sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def _private_path(rel:Path):
    if any(part.lower() in PRIVATE_DIR_NAMES or part.lower().endswith('_sealed_private') for part in rel.parts[:-1]): return True
    if rel.name in PRIVATE_FILE_NAMES: return True
    return False

def archive(root,mode):
    root=Path(root).resolve(); mode=str(mode).lower()
    if mode not in {'blind','revealed'}: raise ValueError('mode must be blind or revealed')
    if not root.is_dir(): raise FileNotFoundError(root)
    # The shareable archives live one directory above the project root, matching the SST output convention.
    project=root.parent
    dest=project.parent/f'{root.name}_{mode.upper()}.zip'
    rows=[]
    files=[]
    for p in sorted((q for q in root.rglob('*') if q.is_file()),key=lambda q:q.as_posix().lower()):
        rel=p.relative_to(root)
        if mode=='blind' and _private_path(rel): continue
        if mode=='blind' and rel.name in {'REVEAL_SUMMARY.json','ARCHIVE_REVEALED_MANIFEST.json'}: continue
        files.append((p,rel)); rows.append({'path':rel.as_posix(),'sha256':_sha(p),'bytes':p.stat().st_size})
    manifest={'format':'SST-TREFOIL-OUTPUT-ARCHIVE-1','mode':mode.upper(),'root_name':root.name,
              'file_count':len(rows),'private_material_included':mode=='revealed','files':rows}
    mp=root/f'ARCHIVE_{mode.upper()}_MANIFEST.json'
    mp.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    # Recompute list to include this mode's public manifest, while still respecting exclusions.
    files=[]
    for p in sorted((q for q in root.rglob('*') if q.is_file()),key=lambda q:q.as_posix().lower()):
        rel=p.relative_to(root)
        if mode=='blind' and _private_path(rel): continue
        if mode=='blind' and rel.name in {'REVEAL_SUMMARY.json','ARCHIVE_REVEALED_MANIFEST.json'}: continue
        files.append((p,rel))
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p,rel in files: z.write(p,arcname=f'{root.name}/{rel.as_posix()}')
    print(json.dumps({'mode':mode.upper(),'archive':str(dest),'sha256':_sha(dest),'files':len(files)},indent=2))
    return dest

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('mode',choices=['blind','revealed']); ap.add_argument('root'); a=ap.parse_args(argv)
    archive(a.root,a.mode); return 0

if __name__=='__main__': raise SystemExit(main())
