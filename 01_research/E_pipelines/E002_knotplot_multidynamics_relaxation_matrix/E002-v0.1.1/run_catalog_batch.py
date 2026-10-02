from __future__ import annotations
import argparse,json,sys,re
from pathlib import Path
from datetime import datetime
from run_matrix_batch import resolve_shortcut, run_one_script, DEFAULT_SHORTCUT
from catalog_recipe_support import load_recipe, recipe_hash
ROOT=Path(__file__).resolve().parent

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--shortcut',type=Path,default=DEFAULT_SHORTCUT); ap.add_argument('--one'); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args(argv)
    try: recipe=load_recipe(ROOT/'catalog_recipe.json',False)
    except Exception as e: print(f'ERROR: {e}. Select/approve recipe before catalog run.',file=sys.stderr); return 2
    rh=recipe_hash(recipe)
    scripts=sorted((ROOT/'catalog').glob('*/build_*.kpc'))
    if a.one: scripts=[p for p in scripts if p.parent.name==a.one or p.name==a.one]
    if not scripts: print('ERROR: no catalog scripts; run run_prepare_catalog.cmd first',file=sys.stderr); return 2
    for p in scripts:
        t=p.read_text(errors='replace'); m=re.search(r'^% RECIPE_SHA256 (\S+)',t,re.M)
        if not m or m.group(1)!=rh: print(f'ERROR: stale/unlocked catalog script: {p}',file=sys.stderr); return 3
    try: exe,wd=resolve_shortcut(a.shortcut.resolve())
    except Exception as e: print(f'ERROR: {e}',file=sys.stderr); return 1
    stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
    print(f'Catalog recipe: {recipe["recipe_id"]} SHA={rh} scripts={len(scripts)}')
    for i,p in enumerate(scripts,1):
        cid=p.parent.name; print(f'\n--- [{i}/{len(scripts)}] {cid} ---')
        rc=run_one_script(exe=exe,workdir=wd,script=p,log_path=ROOT/'catalog_logs'/f'{cid}_console.log',audit_path=ROOT/'catalog_logs'/f'{cid}_audit.json',archive_dir=ROOT/'archive'/stamp/'catalog'/cid,dry_run=a.dry_run)
        if rc: return rc
    print('CATALOG RUN PASS'); return 0
if __name__=='__main__': raise SystemExit(main())
