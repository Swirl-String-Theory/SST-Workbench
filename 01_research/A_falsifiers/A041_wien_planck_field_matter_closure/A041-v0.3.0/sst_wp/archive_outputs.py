from __future__ import annotations
import argparse, zipfile
from pathlib import Path

EXCLUDE_BLIND_TOKENS=(
    'private','reveal','raw_observations','campaign_private','selected_inputs',
    'dataset_inventory','atlas_parameter_manifest'
)

def safe_for_blind(rel: Path)->bool:
    s=rel.as_posix().lower()
    return not any(tok in s for tok in EXCLUDE_BLIND_TOKENS)

def make_archive(root: Path, dest: Path, mode: str):
    root=root.resolve();dest=dest.resolve();dest.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(root.rglob('*')):
            if not p.is_file(): continue
            rel=p.relative_to(root)
            if mode=='blind' and not safe_for_blind(rel): continue
            z.write(p,arcname=(root.name+'/'+rel.as_posix()))
    return dest

def main():
    ap=argparse.ArgumentParser();ap.add_argument('root');ap.add_argument('--mode',choices=['blind','revealed'],required=True);ap.add_argument('--dest',required=True);a=ap.parse_args()
    d=make_archive(Path(a.root),Path(a.dest),a.mode);print(d)
if __name__=='__main__': main()
