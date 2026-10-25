"""Conservative installer. Dry-run by default. Only 512/1024/2048 qualified cases.
Example: python install_candidates.py --target C:\\...\\A006-v0.5.0
         python install_candidates.py --target C:\\...\\A006-v0.5.0 --apply
"""
from __future__ import annotations
import argparse,datetime,json,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--target',type=Path,required=True)
    ap.add_argument('--apply',action='store_true');ap.add_argument('--allow-multiple',action='store_true')
    args=ap.parse_args();target=args.target.resolve()
    if not target.is_dir():raise SystemExit(f'Not a directory: {target}')
    if not (target.name.lower().startswith('a006') or 'a006' in str(target).lower()):
        raise SystemExit('Refusing target outside A006 tree')
    m=json.loads((ROOT/'MANIFEST.json').read_text())
    candidates=[c for c in m['cases'] if c['release_status']=='STATIC_GEOMETRY_CANDIDATE_NOT_EULER_CERTIFIED']
    assert len(candidates)==36
    backup=target/f'BACKUP_TWIST_SEEDS_v050d_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}'
    ops=[];unmatched=[]
    existing_assets=[p for p in target.rglob("*") if p.is_file()]
    # Only matching existing output assets; never touch source snapshots or frozen originals.
    for c in candidates:
        for typ,fname in (('xyz',c['file']),('kpt',c['kpt_filename'])):
            source=ROOT/'REPLACEMENTS'/fname
            matches=[]
            for path in existing_assets:
                if not path.is_file() or path.suffix.lower()!=('.'+typ):continue
                rel=str(path.relative_to(target)).lower().replace('\\','/')
                if any(k in rel for k in ['original_frozen','patch_backups','backup_twist_seeds','quarantine','source_snapshots']):continue
                if path.name.lower()==fname.lower():matches.append(path)
                if c['branch']=='ORIG' and path.name.lower()==f"{c['name']}_n{c['count']:04d}.{typ}":
                    if '/output/' in '/'+rel or rel.startswith('output/'):
                        matches.append(path)
            if not matches:unmatched.append(fname)
            if len(matches)>1 and not args.allow_multiple:
                raise SystemExit(f'{fname}: multiple existing matches; specify --allow-multiple to update all. Aborting.')
            for path in matches:ops.append((source,path))
    print(json.dumps({'status':'DRY_RUN' if not args.apply else 'APPLY','target':str(target),
        'planned_updates':len(ops),'unmatched_assets':len(unmatched),'backup_root':str(backup),
        'matched':[str(p.relative_to(target)) for _,p in ops], 'unmatched':unmatched},indent=2))
    if not args.apply:return
    if not ops:raise SystemExit('No existing assets matched. No changes made.')
    backup.mkdir(parents=True,exist_ok=False)
    log=[]
    for source,existing in ops:
        rel=existing.relative_to(target);b=backup/rel;b.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(existing,b)
        import os
        temp=existing.with_name(existing.name+'.v050d_tmp')
        shutil.copy2(source,temp);os.replace(temp,existing)
        log.append({'asset':str(rel),'backup':str(b.relative_to(target)),
                    'source_patch':source.name,'sha256_after':hashlib.sha256(existing.read_bytes()).hexdigest()})
    (backup/'INSTALL_LOG.json').write_text(json.dumps(log,indent=2)+'\n')
    print('Applied',len(ops),'updates; backups in',backup)

if __name__=='__main__':main()
